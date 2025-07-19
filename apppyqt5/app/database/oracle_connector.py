"""
Módulo de banco de dados para conexão com Oracle.
Implementa a conexão real com o banco de dados Oracle, 
com fallback para simulação caso haja erro.
"""
import os
import sys
import datetime

import pandas as pd
import oracledb

from app.utils.logger import log_database_operation, log_action
from app.utils.performance import measure_performance

# ——————————————————————————————————————————————————————————————————————————————
# Força protocolo antigo compatível com Oracle 11g/12c para evitar ORA-28041
os.environ["ORA_SECURITY_VERSION"] = "11"
os.environ["ORA_CLIENT_VERIFIER"]  = "0"
# ——————————————————————————————————————————————————————————————————————————————

# Define o caminho para o Instant Client
if getattr(sys, 'frozen', False):
    lib_path = os.path.join(os.path.dirname(sys.executable), "instantclient_23_7")
else:
    lib_path = os.path.join(os.path.dirname(__file__), "instantclient_23_7")

# Em Windows, adiciona o diretório de DLLs para resolver dependências nativas
if hasattr(os, "add_dll_directory"):
    os.add_dll_directory(lib_path)

# Inicializa o Oracle Instant Client apenas uma vez
if not getattr(oracledb, "_client_initialized", False):
    try:
        oracledb.init_oracle_client(lib_dir=lib_path)
    except oracledb.ProgrammingError as e:
        # Ignora apenas o erro de re-inicialização
        if "init_oracle_client() was already called" not in str(e):
            raise
    else:
        # Marca como já inicializado
        setattr(oracledb, "_client_initialized", True)

# ——————————————————————————————————————————————————————————————————————————————
# Parâmetros padrão de conexão (ajuste para produção)
ORACLE_USER     = "PPAPRT_AUT"
ORACLE_PASSWORD = "FFG926Y99"
ORACLE_DSN      = "192.168.35.221:1535/ppartp.cpfl.com.br"
# ——————————————————————————————————————————————————————————————————————————————

@measure_performance
@log_database_operation
def consulta_notas_oracle(oracle_user: str = None,
                          oracle_password: str = None,
                          oracle_dsn: str = None) -> list[dict]:
    """
    Consulta notas técnicas no banco Oracle.
    Se houver falha, retorna novamente (simulação).
    """
    # Usa valores padrão se não foram fornecidos
    user = oracle_user     or ORACLE_USER
    pwd  = oracle_password or ORACLE_PASSWORD
    dsn  = oracle_dsn      or ORACLE_DSN

    query = """
SELECT
    p.cd_projeto,
    cd_uc,
    vl_motor,
    vl_demanda,
    vl_potencia,
    vl_trafo,
    cd_tensao,
    cd_classificacao,
    cd_classe,
    id_subclasse,
    dt_cadastro,
    cd_usuario_externo,
    nr_atividade,
    id_cliente,
    dt_art,
    dt_ligacao_prevista,
    cd_atividade,
    cd_empresa,
    vl_demanda_acrescimo,
    vl_trafo_acrescimo,
    vl_potencia_acrescimo,
    dt_desligamento,
    dt_religacao,
    hr_desligamento,
    hr_religacao,
    ds_observacao,
    vl_potencia_gerador,
    CASE
            WHEN vl_potencia_gerador >= 75 THEN 'GA'
            ELSE 'O&M'
    END AS PROJ_RESP,
    vl_fator_potencia,
    vl_tensao_saida,
    in_protecao,
    in_optante,
    CASE
        WHEN ad_info.cd_sistema_compensacao = '01' THEN 'Autoconsumo Local'
        WHEN ad_info.cd_sistema_compensacao = '02' THEN 'Grupo A'
        WHEN ad_info.cd_sistema_compensacao = '03' THEN 'Multiplas Unidades Consumidoras'
        WHEN ad_info.cd_sistema_compensacao = '04' THEN 'Geracao Compartilhada'
        ELSE 'Autoconsumo Remoto'
    END AS mod_pp,
    CCSP_POTMICROGER,
    user_name,
    ds_titulo,
    nr_sa,
    CASE
        WHEN ccsp_fonteger = '001' THEN 'Energia Hidráulica'
        WHEN ccsp_fonteger = '002' THEN 'Energia Solar'
        WHEN ccsp_fonteger = '003' THEN 'Energia Eólica'
        WHEN ccsp_fonteger = '004' THEN 'Energia Biomassa'
        ELSE 'Energia Cogeração Qualificada'
    END AS ccsp_fonteger,
    nm_responsavel_campo,
    fg_status,
    sa_viabilidade,
    cd_tensao_fornecimento,
    cd_tensao_contrato,
    cd_tensao_medicao,
    class_name,
    fg_motor,
    fg_disjuntor,
    cd_cliente,
    nr_nota_servico,
    fg_optante,
    cd_profissional_responsavel,
    nr_solicitacao,
    cd_tipo_fornecimento,
    nr_transformadores,
    nr_lotes,
    nr_postes,
    nr_lampadas,
    vl_potencia_iluminacao_publica,
    cd_tipo_rede,
    fg_administracao,
    vl_carga_administracao,
    vl_demanda_administracao,
    vl_demanda_total_apartamentos,
    nm_edificio,
    nr_atividade_proj_relacionado,
    cd_padrao_rede_distribuicao,
    cd_tipo_ocupacao,
    cd_motivo_ocupacao,
    nr_pontos,
    fg_possui_analise_terceiros,
    nr_geradores,
    cd_tipo_conexao,
    nr_fone_responsavel_campo,
    in_viabilidade,
    in_projeto,
    id_equipamento_ref,
    nr_equipamento_referencia,
    id_finalidade_solic,
    in_ciente_ence,
    cd_profissional_executor,
    nr_art,
    qtd_pontos,
    tp_movimentacao,
    botaocontratoenviado,
    botaosolicitarvistoria,
    controlestatusdeinspecao,
    primeiroreorcamento,
    fg_consulta,
    anexonull,
    
    -- Colunas agregadas condicionalmente
    MAX(CASE WHEN ps.cd_status IN ('220', '224') THEN 'Sim' ELSE 'Não' END) AS Aguarda_Analise_Comercial,
    MAX(CASE WHEN ps.cd_status IN ('273','222','300','2400','2500','510','200','276') THEN 'Sim' ELSE 'Não' END) AS Aguarda_Analise_Tecnica,

    MAX(ps.dt_parecer) AS dt_parecer,
    MAX(ps.cd_subgrupo) AS cd_subgrupo,
    REGEXP_SUBSTR(sg.ds_subgrupo, '[^-]+$', 1, 1) AS BOX_PROJETO,
    MAX(ps.tp_analise) AS tp_analise,
    MAX(sg.ds_subgrupo) AS ds_subgrupo,
    MAX(ccs.ccsp_street) AS RUA_CCS,
    MAX(ccs.ccsp_house_num1) AS NUM_RUA_CCS

FROM
    ppart.projeto p
LEFT JOIN
    ppart.projeto_status ps ON p.cd_projeto = ps.cd_projeto
LEFT JOIN
    ppart.subgrupo sg ON ps.cd_subgrupo = sg.cd_subgrupo
LEFT JOIN (
    SELECT
        ppart_cd_projeto,
        ccsp_city_code,
        ccsp_empresa,
        ccsp_nome_muni_serv,
        ccsp_tipoger,
        ccsp_street,
        ccsp_house_num1,
        ccsp_fonteger,
        ccsp_potmicroger,
        ccsp_cargtotisnt
    FROM
        ppart.xi_gera_atividade_ns
) ccs ON p.cd_projeto = ccs.ppart_cd_projeto
LEFT JOIN
    ppart.projeto_informacoes_adicionais ad_info ON p.cd_projeto = ad_info.cd_projeto

WHERE
    ps.cd_status IN ('220', '224','273','222','300','2400','2500','510','200','276')
    AND p.cd_empresa = '1'
    AND p.cd_classificacao = '61'
    AND dt_cadastro > TO_DATE('01/01/2025', 'DD/MM/YYYY')

GROUP BY
    p.cd_projeto,
    cd_uc,
    vl_motor,
    vl_demanda,
    vl_potencia,
    vl_trafo,
    cd_tensao,
    cd_classificacao,
    cd_classe,
    id_subclasse,
    dt_cadastro,
    cd_usuario_externo,
    nr_atividade,
    id_cliente,
    dt_art,
    dt_ligacao_prevista,
    cd_atividade,
    cd_empresa,
    vl_demanda_acrescimo,
    vl_trafo_acrescimo,
    vl_potencia_acrescimo,
    dt_desligamento,
    dt_religacao,
    hr_desligamento,
    hr_religacao,
    ds_observacao,
    vl_potencia_gerador,
    vl_fator_potencia,
    vl_tensao_saida,
    in_protecao,
    in_optante,
    ad_info.cd_sistema_compensacao,
    user_name,
    ds_titulo,
    nr_sa,
    ccsp_fonteger,
    CCSP_POTMICROGER,
    nm_responsavel_campo,
    fg_status,
    sa_viabilidade,
    cd_tensao_fornecimento,
    cd_tensao_contrato,
    cd_tensao_medicao,
    class_name,
    fg_motor,
    fg_disjuntor,
    cd_cliente,
    nr_nota_servico,
    fg_optante,
    cd_profissional_responsavel,
    nr_solicitacao,
    cd_tipo_fornecimento,
    nr_transformadores,
    nr_lotes,
    nr_postes,
    nr_lampadas,
    vl_potencia_iluminacao_publica,
    cd_tipo_rede,
    fg_administracao,
    vl_carga_administracao,
    vl_demanda_administracao,
    vl_demanda_total_apartamentos,
    nm_edificio,
    nr_atividade_proj_relacionado,
    cd_padrao_rede_distribuicao,
    cd_tipo_ocupacao,
    cd_motivo_ocupacao,
    nr_pontos,
    fg_possui_analise_terceiros,
    nr_geradores,
    cd_tipo_conexao,
    nr_fone_responsavel_campo,
    in_viabilidade,
    in_projeto,
    id_equipamento_ref,
    nr_equipamento_referencia,
    id_finalidade_solic,
    in_ciente_ence,
    cd_profissional_executor,
    nr_art,
    qtd_pontos,
    tp_movimentacao,
    botaocontratoenviado,
    botaosolicitarvistoria,
    controlestatusdeinspecao,
    primeiroreorcamento,
    fg_consulta,
    ds_subgrupo,
    anexonull    
ORDER BY
    dt_cadastro ASC
    """
    try:
        conn   = oracledb.connect(user=user, password=pwd, dsn=dsn)
        cursor = conn.cursor()
        cursor.execute(query)

        cols  = [col[0] for col in cursor.description]  
        rows  = cursor.fetchall()
        conn.close()

        notes = []
        for row in rows:
            rec = {cols[i]: row[i] for i in range(len(cols))}
            if rec.get("DT_CADASTRO"):
                rec["DT_CADASTRO"] = rec["DT_CADASTRO"].strftime("%d-%m-%y")
            rec["tipo"] = "GD"
            notes.append(rec)

        log_action("oracle_query_success", {"count": len(notes)})
        
        return notes

    except Exception as e:
        log_action("oracle_query_error", {"error": str(e)})
        # Em caso de erro, faz fallback (simulação)
        return consulta_notas_oracle()
