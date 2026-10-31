# guilda: distribuição do template como pacote Python

Data: 2026-10-31 · Estado: decisões do mantenedor fechadas; aguardando aprovação final da spec (nada do pacote foi construído)

## Intenção e por quê

Hoje, usar o template exige clonar o repositório, rodar `install.py`, e repetir clonar/pull/instalar a cada mudança aprovada na `main`. O mantenedor testa features dentro do próprio projeto (skills, agentes, regras, mods, qualquer arquivo da arquitetura do template) e só depois as leva ao template. O ciclo é pesado e não serve a quem não tem o repositório.

Objetivo: publicar o template como o pacote público **`guilda`** (PyPI), instalável com `pip` ou `uv`, com o comando `guilda`, mantendo o comportamento atual e o fluxo de experimentar localmente e propor ao projeto.

## Objetivos

1. `pip install guilda` / `uv tool install guilda` entrega o comando `guilda` com todo o conteúdo do template embutido; não é preciso clonar nada.
2. Tudo que existe hoje continua na primeira versão: `init`, `sync`, `check`, `doctor`, `package`, o atalho `install.py`, o instalador de mods, perfis, papéis, ações, skills, adapters e integrações, com os mesmos parâmetros.
3. `guilda upgrade` atualiza um projeto instalado sem destruir o que o usuário acrescentou e nunca o deixa meio atualizado.
4. `guilda promote` leva uma feature testada localmente ao repositório como uma issue, com os arquivos em um gist.
5. Projetos já instalados com o nome antigo migram para `guilda` pelo próprio `upgrade`.
6. A publicação no PyPI sai de uma pipeline cujo job de publicação só roda após aprovação manual do mantenedor.
7. **A instalação contém unicamente o projeto e o que o torna funcional**: nenhum documento de desenvolvimento (specs, planos, ideação) nem saída de ferramenta chega ao pacote ou aos projetos dos usuários.

## Não objetivos

- Não aceitar pull requests de terceiros; só issues. Um mantenedor analisa.
- Não publicar automaticamente: nenhuma versão chega ao PyPI sem aprovação humana.
- Não fazer cópia de segurança dos arquivos que o `upgrade` sobrescreve.
- Não manter dois nomes (pacote, comando, manifesto) depois da migração.
- Não gerenciar plugins globais do Claude Code, que são independentes do `guilda`.
- Não trazer dependências de Python além da biblioteca padrão.

## Antiobjetivos (falha mesmo que "funcione")

- Um `upgrade` que deixa o projeto em estado misto, com arquivos novos e antigos.
- Um `promote` que publica segredos, caminhos pessoais ou arquivos que o usuário não viu.
- Uma versão no PyPI que ninguém aprovou.
- Perder trabalho local do usuário sem aviso e sem aprovação explícita.
- Um documento de desenvolvimento ou arquivo de ferramenta dentro do pacote ou da instalação (já acontece hoje; ver "O que é instalado").

## Restrições

- Python 3.11 ou superior, só biblioteca padrão, Windows e sistemas POSIX.
- Claude Code e Codex continuam sendo os provedores; os arquivos gerados são os de hoje.
- `promote` exige o `gh` já autenticado; o `guilda` não pede nem guarda token.
- A `main` contém só o template e o que o constrói, testa e publica (ver "Chamadas"). Specs, planos e ferramentas de evolução nunca entram na `main` nem na `develop`.

## Decisões do mantenedor

**Nome e distribuição.** `guilda` em todo lugar: pacote, comando, manifesto. Livre no PyPI e no npm em 2026-10-31; `guild` e `guild-cli` estão ocupados. Pacote público. O repositório já se chama `guilda`. Logo em `assets/logo/` (uma cor, teal).

**Comando.** Mesmos parâmetros de hoje; a primeira versão inclui tudo que o repositório tem hoje.

**Duas atualizações, separadas.** Do **projeto** (arquivos do template dentro dele): `guilda upgrade`, sempre disponível. Do **`guilda`** (instalação global): existe, **desligada por padrão**.

**Regras do `upgrade`.**

- Sem conflito: atualiza.
- Conflito é um arquivo que o usuário modificou **e** que a versão nova também mudou. O `guilda` mostra a lista, avisa que seguir sobrescreve e perde as mudanças locais, e só prossegue com aprovação explícita.
- **Tudo ou nada.** Sem aprovação, nada muda. A razão: os testes rodam numa versão estável publicada, e misturar versões cria um estado que ninguém testou. O risco de seguir é do usuário.
- **Sem backup.** Sem terminal interativo (script, CI): falha mostrando a lista sem gravar nada; só `--yes` aprova. Sempre sugere `guilda promote` antes de perder uma mudança local.
- Arquivos que o usuário acrescentou e o template não conhece nunca são tocados.

**Promover (`guilda promote`).** O usuário termina e testa a feature localmente e roda o comando. Ele empacota os arquivos novos e modificados (o manifesto diz quais são), sobe um gist e abre uma issue no repositório com descrição, documentação e a lista de mudanças necessárias (catálogo, testes, changelog, README). Qualquer pessoa pode usar; terceiros contribuem só por issue; a issue leva só descrição e o link. Antes de publicar, varre segredos e caminhos pessoais, mostra o que será enviado e pede confirmação. O conteúdo da issue e do gist é entrada não confiável: tratado só como dado, e nada é implementado sem aprovação do mantenedor.

**Migração do nome antigo.** O manifesto antigo (`name: engineering-template`) é aceito apenas pelo `upgrade`, que reescreve o nome na mesma operação atômica da atualização. A pasta `.engineering/` não muda. Depois só existe um nome. O marketplace de mods, em **novas** instalações, passa a `guilda-mods`; plugins globais já instalados não são tocados.

**Versionamento.** `policies/versioning.md`: toda mudança que entra na `main` ganha antes uma tag SemVer, criada pelo principal e publicada antes do código.

**Licença: Apache-2.0** (arquivo `LICENSE` criado, titular Allan Kletison Teotonio). Cobre isenção de garantia e de responsabilidade, patente e termos de contribuição, e não concede direitos sobre a marca. Uma licença aberta não transfere autoria; para o mantenedor poder relicenciar, o modelo de issue e o `promote` levam um aceite curto de contribuição (texto sujeito a revisão jurídica). O teste de neutralidade tem exceção só para o `LICENSE`.

## Fluxo de desenvolvimento (gitflow)

- `main`: só versões lançadas, com a tag SemVer antes do código.
- `develop`: integração das features.
- `feature/*`: saem da `develop` e voltam para ela por PR.
- `release/*`: saem da `develop`, vão para a `main` e voltam para a `develop`. `hotfix/*`: saem da `main`.
- Regra de repositório `gitflow-main-develop` (criada): em `main` e `develop`, bloqueia apagar e reescrever histórico e exige PR (sem exigir aprovações); o administrador contorna.
- Regra `tags-semver-protegidas` (criada): tags `v*` só são criadas pelo administrador.
- **Sandbox/TestPyPI: fora do escopo** por decisão do mantenedor. Features passam pela `develop` e saem em `release/*`; o teste antes de publicar acontece localmente e na pipeline.

## Documentos de desenvolvimento (specs, planos)

- Vivem no branch `dev-docs`, sem ligação com o resto do histórico, montado como worktree na pasta fixa `.dev/`. A pasta está no `.gitignore`, então não existe para a `develop` nem para a `main`.
- Specs em `.dev/specs/`, planos em `.dev/plans/`. Ferramentas que escrevem em `docs/superpowers/` apontam para `.dev/`.
- Documento e código ficam em históricos diferentes; a referência é pelo nome da feature.
- Os documentos de desenvolvimento são **públicos**: o branch `dev-docs` é enviado ao GitHub (decisão do mantenedor). Nada sensível pode entrar nele (segredos, códigos de recuperação, caminhos pessoais).
- Testes que varrem o repositório ignoram `.dev/` e `.worktrees/`.

## O que é instalado (lista de permitidos)

Há dois "instalar", e ambos passam a usar lista de permitidos em vez de lista de proibidos.

1. **Conteúdo do pacote** (`pip install guilda`): o código do `guilda`, `core/`, `profiles/`, `adapters/`, `integrations/`, `template.json` e o `LICENSE`. Fora: `docs/`, `assets/`, `tests/`, `.github/`, `.dev/`, `.worktrees/`.
2. **O que `guilda init` copia para um projeto**: hoje `load_source` percorre `core/`, `profiles/`, `adapters/` e `integrations/` inteiros e `render` instala tudo de `core/` em `.engineering/`. Isso já vaza: ao instalar a partir desta pasta, 74 arquivos (606 KiB) de `core/graphify-out/` iriam para cada projeto, um deles com o caminho absoluto `C:\dev\engineering-template`. A instalação passa a vir de uma lista explícita de arquivos, e um teste compara o conjunto instalado com uma lista commitada; mudar o que é instalado exige editar essa lista de propósito.
3. **Vigias automáticos.** A pipeline falha em PR para `develop` ou `main` se aparecer `docs/superpowers/`, `plans/`, `specs/`, `graphify-out/` ou `.worktrees/`, e confere o conteúdo do pacote construído contra a lista.
4. `graphify-out/` e saídas de ferramenta entram no `.gitignore`.

## Publicação

- Pipeline dispara na tag `vX.Y.Z`, roda testes (Python 3.11, 3.12 e 3.13, Windows e Linux), constrói e prepara a distribuição.
- O job de publicação usa o ambiente `pypi` do GitHub: **só o mantenedor aprova**; administradores não contornam; a autoaprovação está permitida (senão o único revisor não aprova a própria execução); o ambiente aceita só tags `v*`. Publicação confiável por OIDC, sem token guardado.
- O job confere que a tag, a versão em `template.json` e a versão do pacote são iguais, e que o commit da tag já está na `main`. Como a tag sobe antes do código, o mantenedor aprova depois que o código chegar.
- **Já configurado:** publicador pendente no PyPI (projeto `guilda`, dono `allankltsn`, repositório `guilda`, fluxo `release.yml`, ambiente `pypi`); ambiente `pypi` no GitHub; regras de branches e de tags. O nome do fluxo de trabalho no PyPI é `release.yml`; renomear o arquivo, o repositório ou o dono quebra a publicação.

## Chamadas do desenho (decisões minhas, a revisar)

1. **Primeira versão `2.0.0`.** Mudar o contrato que os projetos instalados usam (nome no manifesto, ponto de entrada) é MAJOR pela regra de versionamento.
2. **Comandos.** Mantém `init`, `sync`, `check`, `doctor`, `package`. `sync` fica como primitiva estrita e não interativa; `upgrade` é o comando de uso humano (aprovação, migração, aviso de versão). Acrescenta `install <projeto>`, `mod`, `promote` e `self-update`.
3. **Classificação por arquivo no `upgrade`** (arquivo do usuário, hash no manifesto, arquivo da versão nova): intocado e igual → nada; intocado e mudou → atualiza; modificado e o template não mudou → **mantém o do usuário** e informa; modificado e o template mudou → conflito. Isso muda o `sync` de hoje, que aborta em qualquer modificação. Um arquivo do usuário que o template passa a entregar no mesmo caminho, com conteúdo diferente, também é conflito.
4. **Verificação automática de versão** desligada por padrão; ligada, no máximo uma consulta por dia ao PyPI, avisando ou atualizando. `self-update` existe sempre. Com ela desligada o `guilda` não faz acesso de rede por conta própria, salvo `promote` e o que o usuário pedir.
5. **Gist secreto** (sem listagem, acessível por link); a issue pública leva o link.
6. **Embalagem.** A estrutura do repositório se mantém; a distribuição embute `core/`, `profiles/`, `adapters/`, `integrations/`, `template.json` e os arquivos dos mods dentro do pacote, e o código os encontra pelo pacote (hoje `SOURCE = Path(__file__).parents[1]`).
7. **O que pode existir na `main`:** o template, mais o que o constrói, testa e publica (`pyproject.toml`, `LICENSE`, `.github/workflows/`, `tests/`, `README` e `CHANGELOG`). Isso entra na `main` porque a tag e o pacote saem dela; apenas o que está na lista de permitidos vai na distribuição. **Confirmado pelo mantenedor.**
8. Backend de empacotamento, divisão em módulos, formato do arquivo de configuração do usuário, padrões da varredura de segredos, texto das mensagens, modelo de issue e estratégia de testes do `upgrade` ficam para quem constrói.

## Estado atual do repositório (2026-10-31)

- Enviados ao GitHub, nesta ordem (tag antes do código): tags `v1.2.0` e `v1.3.0`, depois a `main` local (agora em `e347a85`, release 1.3.0). O `develop` foi criado a partir dela e está protegido. O envio da `main` passou pela regra de PR por contorno do administrador, previsto na regra.
- O branch local `release/1.3.0` não foi enviado.
- Mudanças não commitadas na `main` local: skills `dark-pipeline-svg` e `readme-styling`, `assets/`, `docs/diagramas.md`, regras de quadro vivo e `versioning`, instalador de mods, `LICENSE`, exceções nos testes e `.gitignore`. Elas devem entrar por `feature/*` na `develop`, não direto na `main`.

## Decisões fechadas

1. Sandbox/TestPyPI fora do escopo.
2. Envio das tags e da `main` autorizado e feito; `develop` criado.
3. `main` = template mais o que o constrói, testa e publica.
4. Documentos de desenvolvimento públicos.

## Pendência

Aprovação final desta spec pelo mantenedor, que libera o plano de implementação.
