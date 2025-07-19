"""
Constantes e definições para o sistema de análise técnica.
"""

# Definições de flags e seus textos associados
FLAG_INFO = {
    "flag_91_sim": {
    "cabecalho": "Informativo",
    "texto": "Art. 91 selecionado: SIM",
    "indeferimento": False  # Indica que esta flag não causa indeferimento
},
"flag_91_nao": {
    "cabecalho": "Informativo",
    "texto": "Art. 91 selecionado: NÃO",
    "indeferimento": False  # Indica que esta flag não causa indeferimento
},
    "flag_anexoe": {
        "cabecalho": "-----(x) FORMULÁRIO ANEXO E",
        "texto": "Anexo E não enviado."
    },
    25: {
        "cabecalho": "-----(x) FORMULÁRIO ANEXO E:",
        "texto": "Anexo E ilegível."
    },
    26: {
        "cabecalho": "-----(x) FORMULÁRIO ANEXO E:",
        "texto": "Conforme GED 15303, enviar anexo E atualizado."
    },
    7: {
        "cabecalho": "-----(x) FORMULÁRIO ANEXO E:",
        "texto": "A UC geradora diverge da UC indicada no projeto."
    },
    8: {
        "cabecalho": "-----(x) FORMULÁRIO ANEXO G:",
        "texto": "A UC indicada no 'Anexo G' não pertence a mesma área de concessão da unidade geradora."
    },
    9: {
        "cabecalho": "-----(x) FORMULÁRIO ANEXO G:",
        "texto": "A UC é do tipo B Optante ou Cliente Livre."
    },
    10: {
        "cabecalho": "-----(x) FORMULÁRIO ANEXO G:",
        "texto": "A UC indicada no 'Anexo G' está com o fornecimento de energia SUSPENSO, o que impossibilita o recebimento de créditos nas faturas de energia."
    },
    11: {
        "cabecalho": "-----(x) FORMULÁRIO ANEXO G:",
        "texto": "Uma das instalações indicadas no 'Anexo G' não pertence ao mesmo titular da unidade geradora."
    },
    12: {
        "cabecalho": "-----(x) FORMULÁRIO ANEXO G:",
        "texto": "As instalações indicadas no 'Anexo G' devem pertencer a mesma área de concessão da instalação geradora e serem do mesmo/raiz de CNPJ. Indicar a porcentagem, a soma total deve ser 100%."
    },
    1: {
        "cabecalho": "-----(x) CAPA DO SITE PROJETOS PARTICULARES:",
        "texto": "O número da UC divergente entre documentos e/ou site."
    },
    2: {
        "cabecalho": "-----(x) STATUS DA INSTALAÇÂO",
        "texto": "A UC está com o fornecimento de energia SUSPENSO e dessa forma não há como conectar o sistema de geração. Orientar o cliente a entrar em contato com 0800 010 1010 para regularizar o status da instalação."
    },
    3: {
        "cabecalho": "-----(x) CAPA DO SITE PROJETOS PARTICULARES:",
        "texto": "Tipo de geração indicado no site não confere com o anexo E."
    },
    23: {
        "cabecalho": "-----(x) CAPA DO SITE PROJETOS PARTICULARES:",
        "texto": "Modalidade de compensação local indicada no site não confere com o anexo E."
    },
    22: {
        "cabecalho": "-----(x) DOCUMENTOS PARA ANÁLISE COMERCIAL:",
        "texto": "Enviar Contrato Social/Estatuto Social."
    },
    21: {
        "cabecalho": "-----(x) DOCUMENTOS PARA ANÁLISE COMERCIAL:",
        "texto": "Enviar Cartão do CNPJ da Receita Federal."
    },
    17: {
        "cabecalho": "-----(x) DOCUMENTOS PARA ANÁLISE COMERCIAL:",
        "texto": "Enviar Documento Oficial, frente e verso (foto e assinatura), do representante do CNPJ."
    },
    18: {
        "cabecalho": "-----(x) DOCUMENTOS PARA ANÁLISE COMERCIAL:",
        "texto": "Enviar Procuração com firma reconhecida em Cartório ou, com assinatura digital seguida de folha de certificação, onde constam os dados do certificado e informações de e-mail/data/hora da assinatura."
    },
    20: {
        "cabecalho": "-----(x) DOCUMENTOS PARA ANÁLISE COMERCIAL:",
        "texto": "Enviar Ata de Assembleia de eleição/nomeação."
    },
    24: {
        "cabecalho": "-----(x) CAPA DO SITE PROJETOS PARTICULARES:",
        "texto": "Modalidade de compensação remota indicada no site não confere com o anexo E."
    },
    28: {
        "cabecalho": "-----(x) FORMULÁRIO ANEXO E",
        "texto": "Ao assinalar a opção do Fast Track, o limite de potência da geração é 7,5 kW."
    },
    29: {
        "cabecalho": "-----(x) SITUAÇÃO CADASTRAL",
        "texto": "O cliente não possuí contrato ativo no sistema e, caso tenha pedido uma ligação nova, deve solicitar a reprogramação da mesma, e posteriormente entrar com nova atividade para dar continuidade no projeto. Favor entrar em contato com 0800 010 1010 para regularizar o status da instalação."
    },
    30: {
        "cabecalho": "-----(x) CAPA DO SITE PROJETOS PARTICULARES:",
        "texto": "A potência indicada na capa do projeto é divergente do Anexo E."
    },
    31: {
        "cabecalho": "-----(x) FORMULÁRIO ANEXO E",
        "texto": "Ao assinalar a opção do Fast Track, a unidade consumidora fica restrita a modalidade de geração local."
    },
    4: {
        "cabecalho": "-----(x) FORMULÁRIO ANEXO E:",
        "texto": "Itens obrigatórios (4.4 e 4.6) não foram marcados no Fast Track."
    },
    5: {
        "cabecalho": "-----(x) FORMULÁRIO ANEXO E",
        "texto": "Item 6 (Fast Track) não foi assinado. Favor enviar o Anexo E devidamente assinado digitalmente ou com assinatura manuscrita original. Não serão aceitas assinaturas coladas ou inseridas como imagem no documento."
    },
    6: {
        "cabecalho": "-----(x) FORMULÁRIO ANEXO E:",
        "texto": "Itens obrigatórios (4.4 e 4.6) não foram marcados."
    },
    "flag_cpf": {
        "cabecalho": "-----(x) DOCUMENTOS PARA ANÁLISE COMERCIAL:",
        "texto": "CPF não enviado ou ilegível."
    },
    "flag_doc_pf": {
        "cabecalho": "-----(x) DOCUMENTOS PARA ANÁLISE COMERCIAL:",
        "texto": "Documentação pessoal não enviada ou ilegível."
    },
    15: {
        "cabecalho": "-----(x) DOCUMENTOS PARA ANÁLISE COMERCIAL:",
        "texto": "Enviar Procuração com firma reconhecida em Cartório ou, com assinatura digital seguida de folha de certificação, onde constam os dados do certificado e informações de e-mail/data/hora da assinatura."
    },
    16: {
        "cabecalho": "-----(x) DOCUMENTOS PARA ANÁLISE COMERCIAL:",
        "texto": "Produtor Rural, enviar a CADESP completa e atualizada do CNPJ titular da instalação."
    },
    13: {
        "cabecalho": "-----(x) DOCUMENTOS PARA ANÁLISE COMERCIAL:",
        "texto": "Assinaturas divergem entre os documentos."
    },
    14: {
        "cabecalho": "-----(x) FORMULÁRIO ANEXO E",
        "texto": "A assinatura do 'Anexo E' não confere com a assinatura do Documento Oficial."
    },
    27: {
        "cabecalho": "-----(x) DOCUMENTOS PARA ANÁLISE COMERCIAL:",
        "texto": "Procuração não enviada ou ilegível."
    },
    108: {
        "cabecalho": ".-----(x) FORMULÁRIO ANEXO F:",
        "texto": "O nome do(a) cliente/documento informado no Anexo F é divergente do cadastrado no site PP."
    },
    109: {
        "cabecalho": ".-----(x) FORMULÁRIO ANEXO F:",
        "texto": "O endereço informado no Anexo F diverge do endereço da instalação cadastrado no site PP. Deve verificar a informação sobre nome da rua (logradouro), número do imóvel e município entre documento e cadastro. Apresentar documento com endereço corrigido ou cadastrar nova atividade no endereço conforme consta no documento, se necessário, solicitando atualização cadastral da instalação através dos canais de atendimento."
    },
    111: {
        "cabecalho": ".-----(x) FORMULÁRIO ANEXO F:",
        "texto": "O número de fases (item 2.3) e corrente nominal do disjuntor (item 2.7) preenchidos no anexo F não condizem com a categoria de ligação liberada no sistema para esta instalação. Pedimos corrigir a informação do anexo F, considerando a situação existente."
    },
    112: {
        "cabecalho": ".-----(x) FORMULÁRIO ANEXO F:",
        "texto": "A quantidade de módulos (item 3.1) preenchida no anexo F diverge da cadastrada no site PP. Pedimos apresentar anexo F corrigido ou corrigir a informação cadastrada no site PP."
    },
    113: {
        "cabecalho": ".-----(x) FORMULÁRIO ANEXO F:",
        "texto": "A quantidade de inversores preenchida no anexo F diverge da cadastrada no site PP."
    },
    116: {
        "cabecalho": ".-----(x) FORMULÁRIO ANEXO F:",
        "texto": "A potência dos módulos (item 3.8) preenchida no anexo F diverge da cadastrada no site PP. Pedimos apresentar anexo F corrigido ou corrigir a informação cadastrada no site PP."
    },
    117: {
        "cabecalho": ".-----(x) FORMULÁRIO ANEXO F:",
        "texto": "A potência dos inversores (item 3.9) preenchida no anexo F diverge da cadastrada no site PP. Pedimos apresentar anexo F corrigido ou corrigir a informação cadastrada no site PP."
    },
    118: {
        "cabecalho": ".-----(x) DIAGRAMA UNIFILAR:",
        "texto": "A potência total dos módulos e inversores não é a mesma da informada na capa do site"
    },
    119: {
        "cabecalho": ".-----(x) DIAGRAMA UNIFILAR:",
        "texto": "Modelo dos inversores (itens 3.2/3.3) divergem da cadastrada no site PP"
    },
    120: {
        "cabecalho": ".-----(x) DIAGRAMA UNIFILAR:",
        "texto": "A quantidade de inversores diverge da cadastrada no site PP."
    },
    121: {
        "cabecalho": ".-----(x) DIAGRAMA UNIFILAR:",
        "texto": "modelo dos módulos (itens 3.2/3.3) divergem do cadastrado no site PP."
    },
    127: {
        "cabecalho": ".-----(x) DIAGRAMA UNIFILAR:",
        "texto": "A potência dos módulos (item 3.8) diverge da cadastrada no site PP."
    },
    128: {
        "cabecalho": ".-----(x) DIAGRAMA UNIFILAR:",
        "texto": "A quantidade de módulos (item 3.1) diverge da cadastrada no site PP."
    },
    129: {
        "cabecalho": ".-----(x) DIAGRAMA UNIFILAR:",
        "texto": "O padrão de entrada não está de acordo com o GED 13 e/ou o anexo F."
    },
    130: {
        "cabecalho": ".-----(x) CERTIDÃO DE REGISTRO PROFISSIONAL",
        "texto": "Anexar a certidão de registro profissional e anotações do CREA/CRT demonstrando suas atribuições legais exigíveis para instalações de micro e minigeração distribuída ## conforme GED 15303 - item 6.7.1 e art. 33/REN 1000 ANEEL."
    },
    131: {
        "cabecalho": ".-----(x) CERTIDÃO DE REGISTRO PROFISSIONAL",
        "texto": "A certidão de atribuição técnica e TRT/ART apresentada via site de projetos, não corresponde ao responsável técnico cadastrado no site. ## conforme GED 15303 - item 6.7.1 e art. 33/REN 1000 ANEEL."
    },
    132: {
        "cabecalho": ".-----(x) CERTIDÃO DE REGISTRO PROFISSIONAL",
        "texto": "Deve ser apresentado que o profissional tenha como atribuição o artigo 8 da resolução 218 do CONFEA, ou seja, esta é a atribuição necessária para que o profissional realize atividade de microgeração perante a uma concessionária de energia elétrica ## conforme GED 15303 - item 6.7.1 e art. 33/REN 1000 ANEEL."
    },
    133: {
        "cabecalho": ".-----(x) CERTIDÃO DE REGISTRO PROFISSIONAL",
        "texto": "Anexar ART/TRT de Projeto válida, ao que consta, após consulta ao Site do CREA, não foi possível validar o documento enviado, o numero de ART/TRT não existe no banco de dados do CREA e/ou já foi utilizado em outra atividade. Favor anexar uma ART/TRT valida; Documentos anexados no campo CPFL."
    },
    114: {
        "cabecalho": ".-----(x) FORMULÁRIO ANEXO F",
        "texto": "Modelo dos módulos (itens 3.2/3.3) preenchidos no anexo F divergem da cadastrada no site PP. Pedimos apresentar anexo F corrigido ou corrigir a informação cadastrada no site PP."
    },
    115: {
        "cabecalho": ".-----(x) FORMULÁRIO ANEXO F",
        "texto": "Fabricante/modelo dos módulos(ou inversores) (itens 3.2/3.3) preenchidos no anexo F divergem da cadastrada no site PP. Pedimos apresentar anexo F corrigido ou corrigir a informação cadastrada no site."
    },
    122: {
        "cabecalho": ".-----(x) FORMULÁRIO ANEXO F",
        "texto": "O campo Potência do Gerador do cadastro do site PP deve ser preenchido com o menor valor de potência entre a total de módulos ou inversor(es)."
    },
    123: {
        "cabecalho": ".-----(x) CERTIFICADO DO INMETRO",
        "texto": "Apresentar registro do Inmetro com status ativo."
    },
    125: {
        "cabecalho": ".-----(x) CERTIFICADO DO INMETRO",
        "texto": "Referente ao registro do Inmetro apresentado, este não cumpre os requisitos para identificação da função de AFCI, portanto, há necessidade de apresentar documento que atenda alguma das seguintes opções: I) Declaração de conformidade do fabricante comprovando o cumprimento da Portaria nº 140/2022, citando modelo do inversor; II) Documento que comprove que o produto já estava em estoque ou foi fabricado antes de 1º de dezembro de 2024; ou III) Empregar inversor homologado com a Portaria INMETRO nº 140/22 ou 515/23 ou concessão emitida após 01/12/24."
    },
    124: {
        "cabecalho": ".-----(x) CERTIFICADO DO INMETRO",
        "texto": "O registro do Inmetro apresentado não condiz com o inversor previsto em projeto, pedimos apresentar registro relativo ao equipamento de interesse."
    },
    # 126: {
    #     "cabecalho": ".-----(x) CERTIFICADO DO INMETRO",
    #     "texto": "O documento apresentado para comprovar as questões relacionadas a função de AFCI do inversor não atende aos critérios, portanto, pedimos apresentar documento que atenda alguma das seguintes opções: I) Declaração de conformidade do fabricante comprovando o cumprimento da Portaria nº 140/2022, citando modelo do inversor; II) Documento que comprove que o produto já estava em estoque ou foi fabricado antes de 1º de dezembro de 2024; ou III) Empregar inversor homologado com a Portaria INMETRO nº 140/22 ou 515/23 ou concessão emitida após 01/12/24.​	certificado_inmetro."
    # },
    101: {
        "cabecalho": ".-----(x) ART/TRT",
        "texto": "O documento de responsabilidade técnica foi emitido por outro(a) profissional."
    },
    102: {
        "cabecalho": ".-----(x) ART/TRT",
        "texto": "O nome do(a) cliente informado no documento de responsabilidade técnica é divergente do cadastrado no site PP."
    },
    103: {
        "cabecalho": ".-----(x) ART/TRT",
        "texto": "O endereço da obra informado no documento de responsabilidade técnica diverge do endereço da instalação cadastrado no site PP. Deve verificar a informação sobre nome da rua (logradouro), número do imóvel e município entre documento e cadastro. Apresentar documento com endereço corrigido conforme cadastro ou cadastrar nova atividade no endereço conforme consta no documento, se necessário, solicitando atualização cadastral da instalação através dos canais de atendimento."
    },
    104: {
        "cabecalho": ".-----(x) ART/TRT",
        "texto": "Apresentar documento de responsabilidade técnica com indicação de Projeto ou Projeto e Execução no campo de atividade técnica, pois a atividade deve ser cadastrada pelo profissional responsável pelo projeto"
    },
    105: {
        "cabecalho": ".-----(x) ART/TRT",
        "texto": "Pedimos apresentar documento de responsabilidade técnica registrado e devidamente pago, seja por autenticação mecânica do conselho no documento ou comprovante de pagamento."
    },
    106: {
        "cabecalho": ".-----(x) ART/TRT",
        "texto": "O documento de responsabilidade técnica deve estar devidamente assinado pelo(a) profissional e cliente. Caso o profissional assine pelo cliente, deverá apresentar em conjunto a procuração que estabelece tal poder. Ou ainda, se houver vínculo envolvendo contratante, quando este assinar pelo cliente, deverá apresentar uma procuração também."
    }

}

# Prazos para resposta
PRAZOS = {
    "5_dias": "5 dias úteis",
    "10_dias": "10 dias úteis",
    "15_dias": "15 dias úteis",
    "30_dias": "30 dias úteis"
}

# Feriados nacionais para cálculo de dias úteis
FERIADOS = [
    "2025-01-01",  # Ano Novo
    "2025-02-03",  # Carnaval
    "2025-02-04",  # Carnaval
    "2025-04-18",  # Sexta-feira Santa
    "2025-04-21",  # Tiradentes
    "2025-05-01",  # Dia do Trabalho
    "2025-06-19",  # Corpus Christi
    "2025-09-07",  # Independência
    "2025-10-12",  # Nossa Senhora Aparecida
    "2025-11-02",  # Finados
    "2025-11-15",  # Proclamação da República
    "2025-12-25"   # Natal
]

# Textos padrão para pareceres
PARECER_DEFERIDO = """
Prezado(a) cliente,

Informamos que sua solicitação de acesso para microgeração distribuída foi DEFERIDA.

Você pode prosseguir com a instalação do sistema conforme projeto apresentado.
Após a conclusão da instalação, solicite a vistoria através do site da CPFL.

Atenciosamente,
Equipe de Análise Técnica
"""

PARECER_INDEFERIDO = """
Prezado(a) cliente,

Informamos que sua solicitação de acesso para microgeração distribuída foi INDEFERIDA pelos motivos listados abaixo.

{pendencias}

Solicitamos que as pendências sejam resolvidas no prazo de {prazo}.
Após as correções, envie novamente a documentação completa através do site da CPFL.

Atenciosamente,
Equipe de Análise Técnica
"""
