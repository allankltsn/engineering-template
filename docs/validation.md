# Validação da entrega

## Escopo

Template completo: 28 papéis (18 de engenharia e plataforma, 10 de produto, design, marca, marketing, frontend sênior, privacidade, usuário leigo e registro), 11 ações, 9 perfis, 17 modelos de documentos, 4 workflows novos (staffing, histórias, usabilidade, polyrepo), 3 políticas novas (modelos, princípios de qualidade, instalações), skill Draw.io e adapters Claude/Codex. Camadas de modelo por papel com override por projeto. Integrações opcionais possuem configuração sanitizada e instruções próprias.

## Evidências executadas

- CLI: check, doctor, init, sync e package exercitados em fixtures locais.
- Suíte Python: 23 testes; um teste de symlink ignorado por privilégio Windows; proteção contra junction validada. Novos testes cobrem camadas de modelo por papel, overrides validados e persistidos no manifesto, papéis de produto e UX (ferramentas e sandbox), usuário leigo somente leitura na camada leve, presença dos workflows, políticas e templates, neutralidade (nenhuma referência a projeto específico) e curadoria de plugins sem instalação.
- Claude 2.1.294: validação nativa estrita do plugin e manifesto aprovada após correções.
- Codex 0.156.1: features list executado; TOML gerado analisado com tomllib. A opção strict-config não é suportada por esse comando.
- Onboarding do plugin: receita documentada executada, contratos disponíveis no consumidor, manifesto não copiado e conflito preservando arquivos.

## Revisões

Implementação e conteúdo tiveram revisão independente de QA, segurança e arquitetura. Corrigidos: confiança indevida em caminhos do manifesto, instruções que poderiam expor segredos, metadados nativos do plugin, carregamento explícito de contexto/perfis, ferramentas de diagnóstico dos revisores e localização dos contratos no consumidor do plugin.

## Limites

Os campos model e model_reasoning_effort gerados, o comportamento de dois usuários leigos reais em paralelo e a rodada de usabilidade completa não foram executados contra um runtime; os dados de popularidade em integrations/plugins/curated.json foram lidos das páginas do GitHub em 2026-10-17 e são sinal, não prova de segurança.


Não foram executadas chamadas de modelo, descoberta/invocação real de cada agente ou skill, ativação de MCP, instalação de plugins externos nem validação visual do GitHub Projects (board, campos e workflows desligados) nem execução real dos scripts de setup contra a API do GitHub. Disponibilidade detectada no PATH não comprova funcionamento. Aprovação estática e testes locais não representam paridade de runtime entre provedores.
