# 🧠 ITBOOST — Bot de Cursos de TI para Discord

O **ITBOOST** é um bot para Discord que ajuda usuários a **encontrar, salvar e explorar cursos de TI** gratuitos e pagos em diversas plataformas como **Udemy, Coursera, edX, Alura, DIO, DataCamp, Hack The Box Academy**, entre outras.  

Com comandos interativos e interface intuitiva, o bot permite pesquisar cursos por categoria ou palavra-chave e salvar favoritos usando um banco de dados SQLite.

---

## 🚀 Funcionalidades

- 🔍 Pesquisa cursos por tema em múltiplas plataformas.  
- 💻 Filtros por áreas: programação, redes, cloud, segurança, banco de dados, ciência de dados e DevOps.  
- 🎯 Comandos *slash* intuitivos (`/cursos_gratuitos`, `/cursos_pagos`, `/pesquisar_cursos`, `/meus_cursos`, `/ajuda`).  
- 💾 Salvamento de cursos favoritos por usuário.  
- ⚡ Web scraping assíncrono para resultados rápidos.  
- 🧠 Busca dedicada para cursos de pentest e segurança da informação.

---

## ⚙️ Tecnologias

- Python 3.10+  
- [discord.py](https://discordpy.readthedocs.io/)  
- aiohttp  
- BeautifulSoup4  
- sqlite3  

---

## 🛠️ Como Usar

1. Crie um bot no [Discord Developer Portal](https://discord.com/developers/applications).  
2. Adicione o token como variável de ambiente:
   ```bash
   export DISCORD_TOKEN="SEU_TOKEN_AQUI"
