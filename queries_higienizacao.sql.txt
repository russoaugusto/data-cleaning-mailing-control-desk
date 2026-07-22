-- Query estratégica para higienizar mailing direto na base de dados corporativa
-- Objetivo: Cruzar a base de clientes com o histórico operacional de tabulações impeditivas

SELECT 
    c.id_cliente,
    c.nome_empresa,
    c.cnpj,
    -- Limpa o telefone direto na consulta eliminando máscaras antigas
    REGEXP_REPLACE(c.telefone, '[^0-9]', '') AS telefone_higienizado,
    c.regiao_ddd
FROM tb_clientes_leads c
LEFT JOIN tb_historico_chamadas h ON c.id_cliente = h.id_cliente
LEFT JOIN tb_lista_nao_perturbe p ON REGEXP_REPLACE(c.telefone, '[^0-9]', '') = p.telefone
WHERE 
    -- Regra 1: Remove telefones vazios ou nitidamente fora do padrão de tamanho
    LENGTH(REGEXP_REPLACE(c.telefone, '[^0-9]', '')) IN (10, 11)
    
    -- Regra 2: Garante que o lead não esteja na lista legal de Não Me Perturbe
    AND p.telefone IS NULL
    
    -- Regra 3: Inteligência Operacional (Exclui tabulações improdutivas recentes)
    -- Se foi tabulado como "Número Inexistente" ou "Recusa Definitiva B2B", expurga do mailing
    AND (h.ultima_tabulacao NOT IN ('NÚMERO INEXISTENTE', 'RECUSA DEFINITIVA', 'PROCON') OR h.ultima_tabulacao IS NULL)
    
    -- Regra 4: Filtro de renitência inteligente (Se ligou hoje e deu ocioso/ocupado, aguarda 24h)
    AND (h.data_ultima_tentativa < CURRENT_DATE OR h.data_ultima_tentativa IS NULL)
ORDER BY c.score_propensao_venda DESC;
