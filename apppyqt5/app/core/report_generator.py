"""
Módulo para geração de pareceres técnicos.
Versão corrigida para gerar pareceres baseados nas flags ativadas.
"""
import datetime
from app.utils.logger import log_action
from app.utils.performance import measure_performance
from string import Formatter


class SafeFormatter(Formatter):
    """
    Formatador seguro que não falha quando uma chave está ausente.
    Retorna a chave entre chaves quando ela não é encontrada.
    """
    def get_value(self, key, args, kwargs):
        if isinstance(key, str):
            return kwargs.get(key, '{' + key + '}')
        else:
            return super().get_value(key, args, kwargs)


class ReportGenerator:
    """
    Gerador de pareceres técnicos baseados nas flags ativadas.
    """
    
    def __init__(self, flags_manager=None):
        """
        Inicializa o gerador de pareceres.
        
        Args:
            flags_manager (FlagsManager, optional): Gerenciador de flags.
        """
        self.flags_manager = flags_manager
        self.parecer_tecnico = ""
        self.template_parecer = """
Prezado(a) Cliente,

Analisamos seu projeto de geração distribuída para a instalação {uc}, atividade {atividade}, {cliente}, e identificamos os seguintes pontos que precisam ser ajustados:

{pendencias}

Solicitamos que os ajustes sejam realizados até {data_limite}.

Após realizar os ajustes solicitados, favor anexar os documentos no site Projetos Particulares.

Atenciosamente,
Equipe de Análise de Projetos - CPFL
"""
        self.formatter = SafeFormatter()
    
    @measure_performance
    def generate_report(self, nota_info=None, uc_info=None, prazo=7):
        """
        Gera um parecer técnico baseado nas flags ativas.
        """
        # 1) log de início
        log_action('report_generation_started', {
            'nota_id': nota_info.get('NR_ATIVIDADE','') if nota_info else None,
            'prazo': prazo
        })

        # 2) coleta flags de indeferimento
        flags_indeferimento = []
        if self.flags_manager:
            active = self.flags_manager.get_active_flags()
            for fid, val in active.items():
                info = self.flags_manager.flags.get(fid, {})
                if val and info.get('indeferimento', True) and fid not in ('flag_91_sim','flag_91_nao'):
                    flags_indeferimento.append(info)

        # 3) agrupa pendências
        grouped = {}
        for f in flags_indeferimento:
            hdr = f.get('cabecalho','OUTROS')
            grouped.setdefault(hdr, []).append(f.get('texto',''))

        # 4) saudação e intro
        report = ["Prezado(a) Cliente,", ""]
        if nota_info and uc_info:
            uc  = nota_info.get('CD_UC','')
            num = nota_info.get('NR_ATIVIDADE','')
            cli = uc_info.get('NOME_RAZAO','') if uc_info.get('SAP_HANA_OK') else ''
            intro = f"Analisamos seu projeto de geração distribuída para a instalação {uc}, atividade {num}"
            if cli:
                intro += f", {cli}"
            intro += (", e identificamos os seguintes pontos que precisam ser ajustados:"
                      if flags_indeferimento else ", e informamos que seu projeto foi DEFERIDO.")
            report += [intro, ""]

        # 5) DEFERIMENTO puro (sem pendências)
        if not flags_indeferimento:
            # extrai potência
            try:
                raw_pot = nota_info.get('CCSP_POTMICROGER') or nota_info.get('pot_sitePP') or 0
                pot = float(raw_pot)
            except:
                pot = 0.0

            # extrai fast_opt do mesmo campo que você gravou acima
            fast_opt = nota_info.get('fast_track', 'não').strip().lower()
            log_action('debug_fast_opt_in_report', {'fast_opt': fast_opt, 'pot': pot})

            # monta a linha única com “APROVADA…”
            if pot <= 7.5:
                if fast_opt == 'sim':
                    linha = (
                        "Seu projeto atende aos requisitos comerciais necessários "
                        "– ANÁLISE COMERCIAL APROVADA, com opção do Fast Track"
                    )
                else:
                    linha = (
                        "Seu projeto atende aos requisitos comerciais necessários "
                        "– ANÁLISE COMERCIAL APROVADA, sem opção do Fast Track"
                    )
            else:
                linha = "Seu projeto atende aos requisitos comerciais necessários."

            report.append(linha)
            report.append("")  # pula uma linha antes do fechamento
            report.append("Atenciosamente,")
            report.append("Equipe de Análise de Projetos - CPFL")

            log_action('report_generation_completed', {
                'nota_id': nota_info.get('NR_ATIVIDADE', ''),
                'status': 'deferido',
                'flags_count': 0
            })
            return "\n".join(report)

        # 6) INDEFERIMENTO (com pendências)
        for hdr, textos in grouped.items():
            report.append(hdr + ":")
            for t in textos:
                report.append(f"- {t}")
            report.append("")

        # ─── Novo bloco: Informações Importantes ───────────────────────────────────────────
        report.append("Informações Importantes:")
        report.append("(A) Esta atividade não tem mais validade, desta forma, pedimos a gentileza de "
                    "movê-la no box de projetos encerrados.")
        report.append("(B) Ao apresentar uma nova atividade, atentar-se à uniformidade das informações "
                    "que constam entre os documentos e os campos preenchíveis no site, além dos "
                    "documentos a serem anexados nessa nova atividade.")
        report.append("Lembre-se: por se tratar de uma nova atividade, toda documentação solicitada nas "
                    "normas da CPFL deve ser apresentada, e utilizar sempre as normas atualizadas no site da CPFL.")
        report.append("Colocamo-nos à disposição para outros esclarecimentos necessários.")
        report.append("")  # quebra de linha antes do prazo
        # ──────────────────────────────────────────────────────────────────────────────────

        # 7) prazo e encerramento
        deadline = (datetime.datetime.now() + datetime.timedelta(days=prazo)).strftime("%d/%m/%Y")
        report += [
            f"Solicitamos que os ajustes sejam realizados até {deadline}.",
            "",
            "Após realizar os ajustes solicitados, favor anexar os documentos no site Projetos Particulares.",
            "",
            "Atenciosamente,",
            "Equipe de Análise de Projetos - CPFL"
        ]

        log_action('report_generation_completed', {
            'nota_id': nota_info.get('NR_ATIVIDADE',''),
            'status': 'pendente',
            'flags_count': len(flags_indeferimento),
            'deadline': deadline
        })

        return "\n".join(report)

    
    def gerar_parecer(self, flags_ativas):
        """
        Gera um parecer técnico baseado nas flags ativadas.
        
        Args:
            flags_ativas (dict): Dicionário de flags ativas.
            
        Returns:
            str: Texto do parecer técnico.
        """
        try:
            # Gera o parecer técnico
            self.gerar_parecer_tecnico(flags_ativas)
            
            # Registra a ação
            log_action('parecer_gerado', {
                'flags_count': len(flags_ativas)
            })
            
            return self.parecer_tecnico
        except Exception as e:
            import traceback
            error_msg = f"Erro ao gerar parecer: {str(e)}\n{traceback.format_exc()}"
            print(error_msg)
            
            # Registra o erro
            log_action('parecer_erro', {
                'error': str(e)
            })
            
            return f"Erro ao gerar parecer: {str(e)}"
    
    def gerar_parecer_tecnico(self, flags_ativas):
        """
        Gera o texto do parecer técnico.
        
        Args:
            flags_ativas (dict): Dicionário de flags ativas.
        """
        # Agrupa as flags por cabeçalho
        pendencias_por_cabecalho = {}
        for flag_id, flag in flags_ativas.items():
            cabecalho = flag.get('cabecalho', 'OUTROS')
            if cabecalho not in pendencias_por_cabecalho:
                pendencias_por_cabecalho[cabecalho] = []
            
            pendencias_por_cabecalho[cabecalho].append(flag.get('texto', ''))
        
        # Formata as pendências
        pendencias_texto = []
        for cabecalho, textos in pendencias_por_cabecalho.items():
            pendencias_texto.append(cabecalho + ":")
            for texto in textos:
                pendencias_texto.append(f"- {texto}")
            pendencias_texto.append("")
        
        # Prepara os dados para o template
        dados_parecer = {
            'uc': '123456789',  # Exemplo, deve ser substituído pelo valor real
            'atividade': '987654321',  # Exemplo, deve ser substituído pelo valor real
            'cliente': 'Nome do Cliente',  # Exemplo, deve ser substituído pelo valor real
            'pendencias': "\n".join(pendencias_texto),
        }
        
        # Calcula a data limite (15 dias úteis)
        data_atual = datetime.datetime.now()
        dias_uteis = 15
        # Adiciona dias úteis (ignorando finais de semana)
        data_limite = data_atual
        dias_adicionados = 0
        while dias_adicionados < dias_uteis:
            data_limite += datetime.timedelta(days=1)
            if data_limite.weekday() < 5:  # 0-4 são dias de semana (seg-sex)
                dias_adicionados += 1
        
        dados_parecer['data_limite'] = data_limite.strftime('%d/%m/%Y')
        
        # Formata o template usando o formatador seguro
        self.parecer_tecnico = self.formatter.format(self.template_parecer, **dados_parecer)
