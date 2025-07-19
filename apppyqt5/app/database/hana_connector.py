# file: app/db/hana_connector.py

import pandas as pd
from hdbcli import dbapi

from app.config import settings
from app.utils.logger import log_database_operation, log_action
from app.utils.performance import measure_performance

# Mapeamento de códigos de tipo de instalação para descrições
id_resumo_dict = {
    '0001': 'Grupo B', '0002': 'Grupo A', '0003': 'Grupo A', '0004': 'Grupo A', '0005': 'Cliente Livre',
    '0006': 'B Optante', '0007': 'Grupo A', '0008': 'Grupo A', '0009': 'Grupo A', '0010': 'Grupo A',
    '0011': 'Cliente Livre', '0012': 'Grupo A', '0013': 'Grupo A', '0014': 'Grupo A',
    '0015': 'Grupo B', '0016': 'B Optante', '0017': 'Grupo A', '0018': 'Grupo A',
    '0019': 'Grupo A', '0020': 'Grupo A', '0021': 'Grupo A', '0022': 'Grupo A',
    '0023': 'Grupo A', '0024': 'Grupo A'
}

id_concessao = {
    'CPFL': 'CPFL Paulista', 'D008': 'RGE', 'D009': 'RGE', 'PIRA': 'CPFL Piratininga',
    'D003': 'CPFL Santa Cruz', 'D004': 'CPFL Santa Cruz', 'D005': 'CPFL Santa Cruz',
    'D006': 'CPFL Santa Cruz', 'D007': 'CPFL Santa Cruz'
}


@measure_performance
@log_database_operation
def consultar_uc_hana(cod_uc: str) -> dict:
    """
    Consulta informações de uma unidade consumidora no SAP HANA, incluindo:
     - dados de instalação (status, contrato, razão social, etc.)
     - endereço completo (ADRC)
     - fase e disjuntor (EVBS.ZZNUMFASE, EVBS.ZZDISJUNTOR)

    Retorna um dicionário com os dados.
    Lança `Exception` em caso de erro de conexão/consulta.
    """
    # pega credenciais
    user     = getattr(settings, 'HANA_USER', None)
    password = getattr(settings, 'HANA_PASSWORD', None)
    address  = getattr(settings, 'HANA_ADDRESS', None)
    port     = getattr(settings, 'HANA_PORT', None)

    # limpa zeros à esquerda
    cod_uc_limpo = str(cod_uc).lstrip('0')

    try:
        conn = dbapi.connect(
            address=address,
            port=port,
            user=user,
            password=password
        )
        cursor = conn.cursor()

        sql = """
        SELECT
          INSTATUS.ANLAGE                            AS COD_INSTALACAO,
          MAX(INSTATUS.ANLAGE_STATUS_TEXT)           AS STATUS_INSTALACAO,
          MAX(EVBS.ZZCATAKIT)                        AS CATEGORIA_INST,
          MAX(EVER.VERTRAG)                          AS NUM_CONTRATO,
          MAX(EVER.ZNOME_RAZAO)                      AS NOME_RAZAO,
          MAX(EANL.ANLART)                           AS COD_TIPO_INSTALACAO,
          MAX(DOC.TAXTYPE)                           AS TIPO_DOCUMENTO,
          MAX(ILOA.BUKRS)                            AS CONCESSAO,
          MAX(DOC.TAXNUM)                            AS NUMERO_DOC,

          -- campos de fase/disjuntor
          MAX(EVBS.ZZNUMFASE)                        AS NUM_FASE,
          MAX(EVBS.ZZDISJUNTOR)                      AS DISJUNTOR,

          -- campos de endereço
          MAX(ADRC.STREET)                           AS STREET,
          MAX(ADRC.HOUSE_NUM1)                       AS HOUSE_NUM1,
          MAX(ADRC.STR_SUPPL1)                       AS COMPLEMENT,
          MAX(ADRC.CITY1)                            AS CITY,
          MAX(ADRC.REGION)                           AS STATE,
          MAX(ADRC.POST_CODE1)                       AS ZIP
        FROM "_SYS_BIC"."accs.views.analytics.dimensions/CA_DIM_INSTALLATION_STATUS" INSTATUS

        LEFT JOIN "SAP_CCS"."EANL"       EANL  ON INSTATUS.ANLAGE = EANL.ANLAGE
        LEFT JOIN "SAP_CCS"."EVBS"       EVBS  ON EANL.VSTELLE   = EVBS.VSTELLE
        LEFT JOIN "SAP_CCS"."EVER"       EVER  ON INSTATUS.ANLAGE = EVER.ANLAGE     AND EVER.AUSZDAT = '99991231'
        LEFT JOIN "SAP_CCS"."DFKKBPTAXNUM" DOC  ON EVER.ZPARTNER  = DOC.PARTNER
        LEFT JOIN "SAP_CCS"."ILOA"       ILOA  ON EVBS.HAUS      = ILOA.TPLNR      AND ILOA.OWNER = '2'
        LEFT JOIN "SAP_CCS"."ADRC"       ADRC  ON ILOA.ADRNR     = ADRC.ADDRNUMBER

        WHERE TRIM(LEADING '0' FROM INSTATUS.ANLAGE) = ?
          AND DOC.TAXTYPE IN ('BR1','BR2')
        GROUP BY INSTATUS.ANLAGE
        """

        cursor.execute(sql, (cod_uc_limpo,))
        rows = cursor.fetchall()
        columns = [col[0] for col in cursor.description]
        cursor.close()
        conn.close()

        if not rows:
            # Sem contrato ativo: retorno válido, mas vazio
            log_action('hana_query_no_results', {'cod_uc': cod_uc})
            return {}

        # monta DataFrame
        df = pd.DataFrame(rows, columns=columns)

        # normaliza e mapeia
        df['TIPO_DOCUMENTO']      = df['TIPO_DOCUMENTO'].map({'BR1':'PJ','BR2':'PF'}).fillna(df['TIPO_DOCUMENTO'])
        df['COD_TIPO_INSTALACAO'] = df['COD_TIPO_INSTALACAO'].map(id_resumo_dict)
        df['CONCESSAO']           = df['CONCESSAO'].map(id_concessao)

        # monta endereço completo
        def monta_endereco(r):
            partes = []
            for fld in ['STREET','HOUSE_NUM1','COMPLEMENT']:
                v = r.get(fld)
                if pd.notna(v) and v:
                    partes.append(str(v).strip())
            cs = ", ".join(
                p for p in (r.get('CITY'), r.get('STATE'), r.get('ZIP'))
                if pd.notna(p) and p
            )
            if cs:
                partes.append(cs)
            return " ".join(partes)

        df['ENDERECO_COMPLETO'] = df.apply(monta_endereco, axis=1)

        # converte para dict e sinaliza OK
        result = df.to_dict(orient='records')[0]
        # result['SAP_HANA_OK'] = True

        log_action('hana_query_success', {'cod_uc': cod_uc})
        return result

    except Exception as e:
        log_action('hana_query_error', {'error': str(e), 'cod_uc': cod_uc})
        # return {'SAP_HANA_OK': False}
        raise
    finally:
         try:
             cursor.close()
             conn.close()
         except:
             pass
