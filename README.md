# Template portátil de engenharia

Pacote real de instruções, especialistas, ações, skills e adapters para Claude Code e Codex. A fonte canônica está neste diretório; a CLI materializa o conteúdo no projeto escolhido. Integrações externas são opcionais e não são instaladas automaticamente.

## Começar

Requer Python 3.11 ou superior. Execute a partir da raiz deste pacote:

```sh
python scripts/template.py init --target <diretorio> --providers claude,codex --profiles base --dry-run
python scripts/template.py init --target <diretorio> --providers claude,codex --profiles base
python scripts/template.py check --target <diretorio>
python scripts/template.py doctor
```

Para atualizar um projeto, use sync com os mesmos argumentos de init. Revise primeiro --dry-run; conflitos locais devem ser resolvidos explicitamente. Perfis adicionais disponíveis no catálogo podem ser combinados com base, por exemplo base,nestjs-mikroorm. Para empacotar o adapter Claude:

```sh
python scripts/template.py package --target <diretorio-de-saida> --provider claude
```

A materialização compartilha regras em .engineering, gera arquivos de projeto Claude e agentes .codex/agents em TOML, além de skills .agents/skills para Codex. O pacote plugin Claude usa agents/, commands/, skills/ e .claude-plugin/ na raiz do plugin. Consulte [compatibilidade](docs/compatibility.md) antes de habilitar.

Para consumir o plugin, siga a [receita do adapter Claude](adapters/claude/README.md): copie os contratos compartilhados para um consumidor sem .engineering, exclua o manifesto do pacote e mescle BOOTSTRAP.md em CLAUDE.md. Essa exportação não é instalação gerenciada; check/sync não se aplicam ao consumidor. A instalação de projeto por init é a alternativa preferencial e evita duplicação de agentes.

## Quem faz o quê

O agente principal é sempre o orquestrador: entende a demanda, seleciona especialistas, mantém o plano, reúne evidências e retorna o resultado. Os especialistas não substituem essa responsabilidade. Expertise responde ao domínio; função responde ao papel naquela etapa, como implementação ou revisão. Um especialista pode revisar no seu domínio; o reviewer consolida uma revisão independente.

| Papel | Expertise |
| --- | --- |
| architect | Arquitetura e decisões técnicas |
| backend | Backend Node e NestJS |
| python | Backend e ferramentas Python |
| aws | Serviços e infraestrutura AWS |
| hosting | Hospedagem e configuração de servidores |
| qa | Qualidade, testes e aceitação |
| security | Segurança de aplicações |
| kubernetes | Clusters e workloads Kubernetes |
| docker | Imagens, containers e execução |
| cicd | Pipelines de integração e entrega |
| devsecops-infra | Segurança de infraestrutura e IaC |
| finops | Custos e eficiência de nuvem |
| sre | Confiabilidade, incidentes e SLOs |
| cloud | Decisões de nuvem e arquitetura multicloud |
| ingress | Entrada de tráfego, proxy e TLS |
| orchestration | Orquestração de serviços e tráfego |
| deployment | Estratégias e gates de release |
| reviewer | Revisão independente e coerência das evidências |

São 17 especialistas de domínio e um reviewer. As oito ações rápidas são qa, security, aws, hosting, kubernetes, sre, cicd e devsecops-infra. O catálogo canônico define o comportamento de cada ação; a disponibilidade e a forma de invocação dependem do adapter. A skill drawio produz e revisa diagramas editáveis vinculados ao trabalho técnico.

## Workflow completo

A demanda passa por entendimento e desenho, planejamento, implementação, revisão independente, correção dos apontamentos e nova revisão até aprovação. QA e segurança são gates explícitos obrigatórios antes da conclusão: a pertinência define o escopo da avaliação, sem omissão silenciosa de nenhum gate. Verificação executada deve ser acompanhada de resultado e limites; arquivos presentes ou testes verdes não comprovam deploy nem aceitação manual.

O gerenciador de projetos é o **GitHub Projects**: cada card é uma issue no repositório onde o trabalho acontece, reunida num único Project com os campos Status, Priority, Agent, Sprint, Due date e Completed at (contrato em `core/workflow/github-projects.md`, perfil `github-projects`). O Status utiliza open, pending, in-progress, in-review, rejected, blocked, completed, accepted e closed. completed registra implementação e verificações concluídas; accepted exige a aceitação prevista; closed encerra o registro. Apontamentos retornam o trabalho à correção; bloqueios devem explicar o impedimento e a próxima ação.

O principal delega somente quando a sessão e o runtime autorizam subagentes. Se a capacidade estiver indisponível, coordene sessões especialistas independentes verificadas ou registre o impedimento; o principal não assume implementação nem parecer especializado. Produção, migrações e operações destrutivas seguem os gates explícitos do projeto e a autorização vigente.

## Integrações opcionais

- [Serena](integrations/serena/README.md): projeto sanitizado e snippets MCP para ambos os provedores.
- [RTK](integrations/rtk/INSTRUCTIONS.md): uso explícito, sem interceptação automática no Codex.
- [Superpowers](integrations/superpowers/README.md): mapeamento das skills de workflow, sem redistribuir plugin.
- [Voltagent](integrations/voltagent/README.md): catálogo dos oito pacotes, configured_not_verified.
- [GitHub Projects](integrations/github-projects/README.md): scripts para criar o Project com os campos do contrato e os labels padrão; workflows automáticos desligados na interface.
- [Configuração Claude](integrations/claude/settings.json): worktree.baseRef=head, sem permissões de commit pré-concedidas.

Não copie credenciais, endpoints privados, caches, memórias ou configurações globais. Nenhuma dependência externa é instalada pelo pacote. A descoberta real de agentes/skills e a paridade de execução entre os provedores continuam pendentes de teste no runtime local.
