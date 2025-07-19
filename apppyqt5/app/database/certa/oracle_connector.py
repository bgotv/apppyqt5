"""
Módulo de banco de dados para conexão com Oracle.
"""
import oracledb
import pandas as pd
from app.config import settings
from app.utils.logger import log_database_operation
from app.utils.performance import measure_performance

@measure_performance
@log_database_operation
def consulta_notas_oracle(oracle_user=None, oracle_password=None, oracle_dsn=None):
    """
    Realiza consulta de notas técnicas no banco Oracle.
    
    Args:
        oracle_user (str, optional): Usuário do Oracle. Se None, usa o valor de settings.
        oracle_password (str, optional): Senha do Oracle. Se None, usa o valor de settings.
        oracle_dsn (str, optional): DSN do Oracle. Se None, usa o valor de settings.
        
    Returns:
        list: Lista de dicionários com as notas técnicas encontradas.
    """
    # Usa valores padrão se não fornecidos
    oracle_user = oracle_user or settings.ORACLE_USER
    oracle_password = oracle_password or settings.ORACLE_PASSWORD
    oracle_dsn = oracle_dsn or settings.ORACLE_DSN
    
    # Consulta completa no banco Oracle
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
    """
    
    try:
        # Inicializa o cliente Oracle se necessário
        lib_path = settings.configure_oracle_client()
        oracledb.init_oracle_client(lib_dir=lib_path)
        
        # Estabelece conexão com o banco
        connection = oracledb.connect(user=oracle_user, password=oracle_password, dsn=oracle_dsn)
        cursor = connection.cursor()
        cursor.execute(query)
        
        # Obtém nomes das colunas e dados
        columns = [col[0] for col in cursor.description]
        rows = cursor.fetchall()
        connection.close()
    except Exception as e:
        print(f"Erro na consulta Oracle: {e}")
        return []
    
    # Processa os resultados
    notes = []
    for row in rows:
        note = {columns[idx]: row[idx] for idx in range(len(columns))}
        if 'DT_CADASTRO' in note and note['DT_CADASTRO'] is not None:
            note['DT_CADASTRO'] = note['DT_CADASTRO'].strftime("%d-%m-%y")
        note['tipo'] = "GD"
        notes.append(note)
    
    return notes
