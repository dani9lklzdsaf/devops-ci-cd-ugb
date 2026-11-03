# UGB - CI/CD com Containers

Projeto de referência para o exercício prático de Melhores Práticas de DevOps. A aplicação usa Python/Flask, MySQL, Docker Compose, NGINX e GitHub Actions com publicação no GitHub Container Registry (GHCR). O deploy remoto pode ser feito em uma VM Ubuntu no Azure.

## 1. Arquitetura

1. O código-fonte é versionado no GitHub.
2. Um push na branch `main` dispara o GitHub Actions.
3. O workflow constrói a imagem Docker da API e publica no GitHub Packages (GHCR).
4. O job de deploy conecta por SSH à VM Azure e atualiza os containers.
5. O NGINX recebe requisições HTTP na porta 80 e encaminha para a API Python.
6. A API consulta e grava dados no MySQL.
7. O Cloudflare gerencia o DNS do domínio apontando para o IP público da VM Azure.

## 2. Executar localmente

Requisitos: Docker Engine e Docker Compose v2.

```bash
cp .env.example .env
# Edite .env e troque as senhas antes de usar fora do ambiente de aula.
docker compose up -d --build
```

Teste no navegador ou terminal:

```bash
curl http://localhost/
curl http://localhost/health
curl -X POST http://localhost/messages \
  -H "Content-Type: application/json" \
  -d '{"content":"Meu primeiro deploy com Docker"}'
curl http://localhost/messages
```

A aplicação ficará disponível em `http://localhost`.

## 3. GitHub e GitHub Packages

1. Crie um repositório no GitHub e envie todos os arquivos deste projeto.
2. Use a branch `main`.
3. Em **Settings > Actions > General**, permita que o workflow tenha acesso de leitura e escrita a packages.
4. Faça um `git push`. O workflow `.github/workflows/ci-cd.yml` constrói a imagem e, em push na `main`, publica no GHCR.
5. A imagem será publicada com o nome `ghcr.io/USUARIO/REPOSITORIO-api`.

O workflow usa `GITHUB_TOKEN`; não é necessário criar um token pessoal para a publicação feita pelo próprio Actions.

## 4. Azure

Crie uma VM Ubuntu no Azure e libere as portas TCP 22 (SSH) e 80 (HTTP) no Network Security Group. Conecte-se à VM e execute o script:

```bash
chmod +x scripts/setup-azure-vm.sh
./scripts/setup-azure-vm.sh
```

Depois, saia e entre novamente na VM para atualizar o grupo Docker. Clone o repositório em `~/ugb-devops` e configure o `.env` com senhas fortes.

Para permitir que a VM baixe a imagem privada do GHCR, autentique o Docker na VM com um Personal Access Token (classic) do GitHub que tenha `read:packages`:

```bash
echo "SEU_TOKEN" | docker login ghcr.io -u SEU_USUARIO --password-stdin
```

No GitHub, cadastre em **Settings > Secrets and variables > Actions**:

- `AZURE_HOST`: IP público da VM.
- `AZURE_USER`: usuário SSH da VM.
- `AZURE_SSH_KEY`: chave privada SSH correspondente à chave instalada na VM.

Ajuste no `docker-compose.yml` a variável `API_IMAGE` para `ghcr.io/USUARIO/REPOSITORIO-api:latest` (ou defina-a no `.env`). O job `deploy-azure` espera que o repositório já esteja clonado em `~/ugb-devops` na VM.

## 5. Cloudflare (DNS)

1. Adicione seu domínio à conta Cloudflare.
2. Crie um registro `A` para o domínio ou subdomínio desejado apontando para o IP público da VM Azure.
3. Para o primeiro teste, deixe o proxy DNS em modo **DNS only**. Depois de validar HTTP, você pode habilitar o proxy.
4. Acesse `http://seu-dominio` e confirme que a resposta chega à API.

Cloudflare faz a resolução DNS/proxy; a aplicação e o NGINX continuam hospedados na VM Azure.

## 6. Comandos úteis

```bash
docker compose ps
docker compose logs -f
docker compose restart api
docker compose down
docker compose down -v  # remove também os dados persistidos do MySQL
```

## 7. Relação com o diagrama da atividade

| Elemento do diagrama | Implementação |
|---|---|
| Código-fonte / GitHub | Repositório Git |
| GitHub Actions | `.github/workflows/ci-cd.yml` |
| GitHub Packages | GitHub Container Registry (GHCR) |
| Imagem API | `app/Dockerfile` |
| DB / MySQL | Serviço `db` no Compose |
| NGINX | `nginx/default.conf` |
| Docker Compose | `docker-compose.yml` |
| Makefile / Scripts | `Makefile` e `scripts/` |
| Azure | VM Ubuntu para executar os containers |
| Cloudflare HTTP 80 / DNS | Registro DNS apontando para a VM |

## 8. Evidências para a entrega

Tire capturas de tela reais depois de executar:

- `docker compose ps` mostrando os três serviços ativos.
- `http://localhost/health` retornando `healthy` e `connected`.
- POST e GET em `/messages` funcionando.
- Execução concluída do workflow no GitHub Actions.
- Imagem publicada na aba Packages do GitHub.
- Aplicação acessível pelo IP/domínio da VM Azure, se o deploy em nuvem fizer parte da avaliação.

**Importante:** não inclua senhas, tokens ou chaves privadas no repositório. O arquivo `.env` está no `.gitignore`; publique apenas `.env.example` sem credenciais reais.
