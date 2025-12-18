# 🚀 Guia Completo - Subir Projeto no Git

## 📋 Pré-requisitos

1. **Instalar Git**
   - Download: https://git-scm.com/download/windows
   - Instalar com configurações padrão

2. **Criar conta no GitHub**
   - Acesse: https://github.com
   - Crie sua conta gratuita

## 🔧 Configuração Inicial do Git

Abra o **Git Bash** ou **PowerShell** e configure:

```bash
# Configurar nome e email (use os mesmos do GitHub)
git config --global user.name "Seu Nome"
git config --global user.email "seu.email@exemplo.com"

# Verificar configuração
git config --list
```

## 📁 Preparar o Projeto

1. **Limpar arquivos desnecessários**
```bash
# Navegar para o projeto
cd C:\Project\projeto-extrator-pdf

# Remover PDFs e Excel (dados sensíveis)
del data\input\*.pdf
del data\output\*.xlsx
```

## 🌐 Criar Repositório no GitHub

1. **Acesse GitHub** → https://github.com
2. **Clique em "New repository"**
3. **Preencha:**
   - Repository name: `projeto-extrator-pdf`
   - Description: `Sistema de extração de dados de extratos bancários PDF`
   - ✅ Public (ou Private se preferir)
   - ❌ NÃO marque "Add a README file" (já temos)
4. **Clique "Create repository"**

## 🔗 Conectar Projeto Local ao GitHub

No **PowerShell** na pasta do projeto:

```bash
# 1. Inicializar repositório Git
git init

# 2. Adicionar arquivos ao staging
git add .

# 3. Fazer primeiro commit
git commit -m "🎉 Projeto inicial: Sistema extrator PDF bancário

- Scripts individuais por banco (BB, Bradesco, Itaú, Caixa, etc.)
- Extrator genérico universal
- Detecção automática de banco
- Extração de metadados completos
- Suporte a 8+ bancos brasileiros"

# 4. Renomear branch para main
git branch -M main

# 5. Conectar ao repositório remoto
git remote add origin https://github.com/SEU_USUARIO/projeto-extrator-pdf.git

# 6. Enviar para GitHub
git push -u origin main
```

## 🔐 Autenticação (se solicitada)

**Opção 1 - Token de Acesso:**
1. GitHub → Settings → Developer settings → Personal access tokens
2. Generate new token (classic)
3. Marque: `repo`, `workflow`
4. Use o token como senha

**Opção 2 - GitHub CLI:**
```bash
# Instalar GitHub CLI
winget install GitHub.cli

# Fazer login
gh auth login
```

## ✅ Verificar se Funcionou

1. **Acesse seu repositório no GitHub**
2. **Verifique se os arquivos estão lá**
3. **README.md deve aparecer na página inicial**

## 🔄 Comandos para Atualizações Futuras

```bash
# Adicionar mudanças
git add .

# Fazer commit
git commit -m "✨ Descrição da mudança"

# Enviar para GitHub
git push
```

## 📝 Exemplo de Mensagens de Commit

```bash
git commit -m "🐛 Corrigir extração Banco do Brasil"
git commit -m "✨ Adicionar suporte Banco Inter"
git commit -m "📚 Atualizar documentação"
git commit -m "🔧 Melhorar detecção automática"
```

## 🆘 Solução de Problemas

**Erro de autenticação:**
```bash
git config --global credential.helper manager-core
```

**Erro de branch:**
```bash
git branch -M main
git push -u origin main
```

**Resetar se algo der errado:**
```bash
rm -rf .git
# Recomeçar do passo "git init"
```

## 🎯 Resultado Final

Seu projeto estará disponível em:
`https://github.com/SEU_USUARIO/projeto-extrator-pdf`

Com:
- ✅ Código fonte completo
- ✅ Documentação
- ✅ Scripts funcionais
- ✅ Estrutura organizada
- ✅ .gitignore configurado (sem dados sensíveis)