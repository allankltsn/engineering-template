# Template portátil de engenharia e gestão de produto

Pacote real de instruções, especialistas, ações, skills e adapters para Claude Code e Codex, **independente de projeto**: a stack, a nuvem e o produto vêm dos perfis e do repositório consumidor, nunca do template. A fonte canônica está neste diretório; a CLI materializa o conteúdo no projeto escolhido. Integrações externas são opcionais e não são instaladas automaticamente.

O agente principal é o **gestor dos especialistas**: entende a demanda, escreve o trabalho como histórias, escolhe os especialistas e o modelo certo para cada um, mantém o plano, reúne evidências e garante a entrega final com qualidade, eficiência, reaproveitamento, idempotência, escalabilidade e tolerância a falhas.

## Começar

Requer Python 3.11 ou superior. Execute a partir da raiz deste pacote:

```sh
python scripts/template.py init --target <diretorio> --providers claude,codex --profiles base --dry-run
python scripts/template.py init --target <diretorio> --providers claude,codex --profiles base,product-team,github-projects
python scripts/template.py check --target <diretorio>
python scripts/template.py doctor
```

Para atualizar um projeto, use `sync` com os mesmos argumentos de `init`. Revise primeiro `--dry-run`; conflitos locais devem ser resolvidos explicitamente. Para empacotar o adapter Claude:

```sh
python scripts/template.py package --target <diretorio-de-saida> --provider claude
```

Para mudar a camada de modelo de um papel neste projeto (regra em `core/policies/models.md`), use `--tier papel=camada`, repetível; fica registrado em `.engineering/project.json` e no manifesto, e papéis de gate nunca descem abaixo de `standard`:

```sh
python scripts/template.py init --target <diretorio> --profiles base --tier reviewer=deep --tier finops=light
```

A materialização compartilha regras em `.engineering`, gera arquivos de projeto Claude (`.claude/agents` com `model`, comandos e skills) e agentes `.codex/agents` em TOML (com `model_reasoning_effort`), além de skills `.agents/skills` para Codex. O pacote plugin Claude usa `agents/`, `commands/`, `skills/` e `.claude-plugin/` na raiz do plugin. Consulte [compatibilidade](docs/compatibility.md) antes de habilitar e a [receita do adapter Claude](adapters/claude/README.md) para consumir o plugin.

## Perfis

| Perfil | Para quê |
| --- | --- |
| `base` | Núcleo neutro de stack: orquestração, gates independentes, evidência |
| `github-projects` | GitHub Projects como gerenciador: nove estados, campos Priority/Type/Estimate/Agent/Sprint, histórias e sub-issues |
| `product-team` | Produto, UX/UI, marca, marketing e frontend sênior, com histórias (DoR/DoD) e rodadas de usabilidade |
| `polyrepo` | Produto em vários repositórios gerenciado a partir de um hub |
| `nestjs-mikroorm`, `python`, `aws-serverless`, `hosting-managed`, `vps-k3s` | Conhecimento de stack, aplicado só quando selecionado |

## Quem faz o quê

O agente principal é sempre o orquestrador e nunca substitui um especialista. Expertise responde ao domínio; função responde ao papel naquela etapa (autor, consultor, QA, revisão, segurança, privacidade, verificador). Ninguém aprova o próprio trabalho.

| Grupo | Papéis (camada de modelo padrão) |
| --- | --- |
| Produto e design | product-owner, ux-researcher, ux-designer, ui-designer, brand-strategist, marketing (standard) |
| Engenharia | architect (deep), backend, python, frontend-senior (standard) |
| Plataforma e nuvem | aws, hosting, kubernetes, docker, cicd, ingress, orchestration, deployment, finops, sre (standard); cloud, devsecops-infra (deep) |
| Qualidade e conformidade | qa, reviewer (standard); security, privacy-compliance (deep) |
| Apoio de baixo custo | lay-user (dois usuários leigos simulados), scribe (registro mecânico) (light) |

São 28 papéis e 11 ações rápidas: qa, security, aws, hosting, kubernetes, sre, cicd, devsecops-infra, **story**, **usability** e **privacy**. O catálogo canônico (`template.json`) define papéis, camadas, ações e skills; a skill drawio produz diagramas editáveis.

## Escolha de especialistas e de modelo

`core/workflow/staffing.md` e `core/policies/models.md` mandam o principal decidir por tarefa, registrando no brief:

- **Especialista**: o mais qualificado para o domínio, a stack e o risco; lacuna vira proposta (adaptar, criar papel ou agente externo aprovado), nunca substituição silenciosa.
- **Camada de modelo**: `deep` (Opus) para os problemas mais difíceis e decisões de segurança, privacidade e arquitetura; `standard` (Sonnet) como padrão do trabalho dos especialistas; `light` (Haiku) para tarefas mecânicas e para os usuários leigos simulados. Sobe de camada por evidência (duas falhas, risco, ambiguidade), desce depois da decisão difícil registrada. Gates nunca ficam abaixo de `standard`, e não se remove gate para economizar tokens.
- **Economia de tokens**: contexto focado, um especialista por pergunta, paralelismo só em escopos disjuntos, reaproveitamento de evidências.

## Gestão de produto no GitHub Projects

O gerenciador é o **GitHub Projects**: cada card é uma issue no repositório onde o trabalho acontece, num único Project com Status (open, pending, in-progress, in-review, rejected, blocked, completed, accepted, closed), Priority, Type, Estimate, Agent, Sprint, Due date e Completed at. Contrato em `core/workflow/github-projects.md`.

Épicos e histórias seguem `core/workflow/user-stories.md` e `core/templates/user-story.md` (ação `/story`): narrativa, regras de negócio com ids, critérios Given/When/Then, fluxo e estados, requisitos não funcionais, ativos e links, metadados, dependências, **Definition of Ready** e **Definition of Done**, estimativa e prioridade. O principal só despacha uma história que cumpre o DoR e só a marca `completed` depois do DoD e da re-execução de uma evidência. `integrations/github-projects` cria o Project, os campos e os labels.

## Usabilidade com usuários leigos simulados

`core/workflow/usability.md` (ação `/usability`): o `ux-researcher` prepara personas e tarefas; **dois** `lay-user` na camada mais fraca, com personas distintas, sem acesso a código, tokens ou contratos, executam as tarefas e relatam onde travaram. Depois o principal e os especialistas fazem um **brainstorm de decisão** com a precedência: segurança e saúde do usuário e leis de privacidade (LGPD/GDPR) e de consumo, depois regras de negócio cruciais, depois usabilidade, depois copy, depois preferência. Pontos que exigem advogado ficam marcados `LEGAL-REVIEW` para o humano. Sem dark patterns. Usuários simulados são um proxy barato, não substituem usuários reais em fluxos de risco.

## Produtos em vários repositórios

`core/workflow/polyrepo.md` e o perfil `polyrepo`: um repositório hub guarda requisitos, ADRs, specs, planos, sprints, runbooks, registro de instalações e decisões; as tarefas ficam em cada repositório de código e voltam ao hub; contratos e pacotes compartilhados são publicados antes dos consumidores; cada repositório recebe o mesmo bootstrap.

## Qualidade de entrega

`core/policies/quality-principles.md`: reaproveitar antes de construir, operações idempotentes, modos de falha nomeados (timeout, retry com backoff, fallback, rollback), escalabilidade e operabilidade, simplicidade e custo, segurança e privacidade por padrão, e verificabilidade com evidência na versão final. `core/policies/installations.md`: nada é instalado sem proposta, critérios de segurança e popularidade, aprovação explícita e registro (registro obrigatório em `docs/operations/registro-instalacoes.md`, modelo em `templates/registro-instalacoes.md`).

## Workflow completo

A demanda vira uma história pronta (DoR), passa por entendimento e desenho, plano e staffing, implementação por especialistas, revisão independente, correção dos apontamentos e nova revisão até aprovação. QA e segurança, e privacidade quando há dados pessoais, são gates explícitos obrigatórios antes da conclusão. Verificação executada deve ser acompanhada de resultado e limites; arquivos presentes ou testes verdes não comprovam deploy nem aceitação manual. `completed` é do principal, após verificar evidência; `accepted` é do usuário.

O principal delega somente quando a sessão e o runtime autorizam subagentes. Se a capacidade estiver indisponível, coordene sessões especialistas independentes verificadas ou registre o impedimento; o principal não assume implementação nem parecer especializado. Produção, migrações e operações destrutivas seguem os gates explícitos do projeto e a autorização vigente.

## Integrações opcionais

- [Plugins e agentes recomendados](integrations/plugins/README.md): curadoria de UI/UX, marca, marketing, produto e frontend com origem, popularidade verificada e comandos; **nada é instalado pelo template**.
- [Serena](integrations/serena/README.md): projeto sanitizado e snippets MCP para ambos os provedores.
- [RTK](integrations/rtk/INSTRUCTIONS.md): uso explícito, sem interceptação automática no Codex.
- [Superpowers](integrations/superpowers/README.md): mapeamento das skills de workflow, sem redistribuir plugin.
- [Voltagent](integrations/voltagent/README.md): catálogo de pacotes de agentes, configured_not_verified.
- [GitHub Projects](integrations/github-projects/README.md): scripts para criar o Project com os campos do contrato e os labels padrão; workflows automáticos desligados na interface.
- [Configuração Claude](integrations/claude/settings.json): worktree.baseRef=head, sem permissões de commit pré-concedidas.

Não copie credenciais, endpoints privados, caches, memórias ou configurações globais. Nenhuma dependência externa é instalada pelo pacote. A descoberta real de agentes/skills, o respeito aos campos de modelo e a paridade de execução entre os provedores continuam pendentes de teste no runtime local.
