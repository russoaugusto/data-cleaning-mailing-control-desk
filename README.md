# Higienizador de Mailing Automatizado para Call Centers (Control Desk)

### ?? Cen rio de Neg¢cio
Em opera‡oes de telemarketing ativo (especialmente no setor B2B corporativo), a eficiˆncia do discador preditivo depende inteiramente da qualidade do banco de dados (mailing). Ligar para n£meros inv lidos, duplicados, sequenciais falsos ou telefones inscritos em listas de restri‡ao legal (como o Procon / Nao Me Perturbe) derruba o *Hit Rate* (taxa de contato humano), aumenta a ociosidade da equipe na ponta e inflaciona os custos de telecomunica‡ao da empresa.

Este reposit¢rio apresenta uma solu‡ao t‚cnica dupla (Python + SQL) desenvolvida para automatizar a limpeza, valida‡ao estrutural e cruzamento de listas antes da carga de mailings em plataformas de discagem em nuvem (como a 3C Plus).

### ?? Funcionalidades T‚cnicas Aplicadas
*   **Limpeza via Expressoes Regulares (Regex):** Expansao e remo‡ao automatizada de m scaras de texto, parˆnteses e hifens em grandes volumes de linhas.
*   **Filtros de Formato e DDD:** Valida‡ao de regras estruturais de telefonia celular e fixa do padrao brasileiro, bloqueando sequˆncias repetidas (ex: n£meros falsos informados em formul rios).
*   **Processamento ETL Eficiente:** Elimina‡ao de registros duplicados idˆnticos na mesma janela de carga utilizando a biblioteca Pandas.
*   **Cruzamento de Dados (Anti-Join):** Limpeza automatizada atrav‚s do cruzamento entre a base de prospec‡ao e listas restritivas legais (Procon).
*   **Regras de Neg¢cio em SQL:** Queries otimizadas prontas para banco de dados relacional, realizando filtros por hist¢rico de tabula‡ao (remover "N£meros Inexistentes" cr“nicos) e regras de tempo de re-discagem (renitˆncia).

### ??? Tecnologias Utilizadas
*   **Python 3.x**
*   **Pandas Library** (Manipula‡ao de DataFrames de alta performance)
*   **SQL (Padrao ANSI / PostgreSQL / MySQL)**
