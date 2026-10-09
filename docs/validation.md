# Validação da entrega

## Escopo

Template completo extraído do catálogo local: 18 especialistas, 8 ações, 7 perfis, 11 modelos de documentos, skill Draw.io e adapters Claude/Codex. Integrações opcionais possuem configuração sanitizada e instruções próprias.

## Evidências executadas

- CLI: check, doctor, init, sync e package exercitados em fixtures locais.
- Suíte Python: 16 testes na suíte; um teste de symlink ignorado por privilégio Windows; proteção contra junction validada.
- Claude 2.1.294: validação nativa estrita do plugin e manifesto aprovada após correções.
- Codex 0.156.1: features list executado; TOML gerado analisado com tomllib. A opção strict-config não é suportada por esse comando.
- Onboarding do plugin: receita documentada executada, contratos disponíveis no consumidor, manifesto não copiado e conflito preservando arquivos.

## Revisões

Implementação e conteúdo tiveram revisão independente de QA, segurança e arquitetura. Corrigidos: confiança indevida em caminhos do manifesto, instruções que poderiam expor segredos, metadados nativos do plugin, carregamento explícito de contexto/perfis, ferramentas de diagnóstico dos revisores e localização dos contratos no consumidor do plugin.

## Limites

Não foram executadas chamadas de modelo, descoberta/invocação real de cada agente ou skill, ativação de MCP, instalação de plugins externos nem validação visual do Kanban. Disponibilidade detectada no PATH não comprova funcionamento. Aprovação estática e testes locais não representam paridade de runtime entre provedores.
