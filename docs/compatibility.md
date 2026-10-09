# Compatibilidade e evidências

Consulta documental: 2026-10-08. Versões locais informadas na preparação: Codex 0.156.1 e Claude Code 2.1.294. Essas versões são contexto de compatibilidade; não representam uma matriz de runtime integralmente validada.

## Codex

[Configuração de subagentes](https://learn.chatgpt.com/docs/agent-configuration/subagents) descreve arquivos TOML em .codex/agents com name, description e developer_instructions. O adapter omite model para herdar a escolha da sessão. agents.enabled é habilitado por padrão segundo essa documentação, mas políticas de sessão ou do processo principal podem restringir delegação e acesso. Um campo de configuração não supera o runtime.

[Skills](https://learn.chatgpt.com/docs/build-skills) documenta .agents/skills para skills do projeto. O adapter materializa a skill drawio nesse caminho. Descoberta e invocação precisam ser verificadas na sessão de destino.

## Claude Code

[Subagentes](https://code.claude.com/docs/en/sub-agents) documenta agentes do projeto em .claude/agents. [Referência de plugins](https://code.claude.com/docs/en/plugins-reference) descreve componentes agents, commands, skills e o manifesto .claude-plugin. O pacote referencia arquivos de agentes explicitamente no manifesto.

As capacidades de um agente de plugin diferem das de agentes de projeto: permissionMode, hooks e mcpServers de agentes de plugin são ignorados conforme a documentação consultada. Por isso a paridade abrange instruções e catálogo; não promete equivalência de sandbox, permissões ou ferramentas. As integrações MCP permanecem configuração separada do projeto.

O consumo do plugin exige também disponibilizar seus contratos COMMON em .engineering na raiz do consumidor e mesclar BOOTSTRAP.md em CLAUDE.md. A [receita do adapter](../adapters/claude/README.md) copia a árvore compartilhada sem manifest.json e aborta se .engineering já existir. É exportação para leitura, sem manifesto de instalação gerenciada: check/sync só se aplicam à raiz do pacote plugin nesse fluxo. Os agentes nativos permanecem no plugin. Presença de contratos e resolução de caminhos numa fixture não comprovam descoberta nativa nem habilitação automática.

## Integrações e escopo da verificação

Serena: presença local do executável e opções start-mcp-server, --project-from-cwd e --context confirmadas pelo help da CLI em 2026-10-08. O contexto ide-assistant e a conexão MCP devem ser confirmados na instalação de destino. O arquivo de projeto deriva de .serena/project.yml sanitizado, sem nome ou memórias do projeto de origem.

RTK: orientação derivada de RTK.md local; não há interceptador Codex incluído. Superpowers é dependência opcional documentada, sem código copiado. Os oito pacotes Voltagent derivam da configuração local e permanecem configured_not_verified. O snippet Kanban deriva das chaves locais, com diretório portátil e os nove estados do contrato atual.

Arquivos e validação estática não comprovam instalação de plugins, conexão de MCP, descoberta de agentes/skills, revisão independente, renderização do board ou deploy. Testes de descoberta e paridade funcional em sessões novas de ambos os provedores permanecem pendentes. Não use a expressão "runtime totalmente verificado" até haver evidência dessas execuções.
