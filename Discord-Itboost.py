import discord
from discord.ext import commands
from discord import app_commands
import os
import sqlite3
import asyncio
import aiohttp
from bs4 import BeautifulSoup
import urllib.parse
from typing import List, Literal


TOKEN = os.getenv("","")  
DB_FILE = "cursos_usuarios.db"
CourseType = Literal["free", "paid", "all"]


SITES_DE_BUSCA = {
    "Udemy": {"url": "https://www.udemy.com/courses/search/?q={}&sort=relevance", "base": "https://www.udemy.com", "filter": "/course/", "type": "mixed"},
    "Coursera": {"url": "https://www.coursera.org/search?query={}", "base": "https://www.coursera.org", "filter": "/learn/", "type": "mixed"},
    "edX": {"url": "https://www.edx.org/search?q={}", "base": "https://www.edx.org", "filter": "/course/", "type": "mixed"},
    "Digital Innovation One": {"url": "https://www.dio.me/browse?search={}", "base": "https://www.dio.me", "filter": "/curso/", "type": "free"},
    "Fund. Bradesco Escola Virtual": {"url": "https://www.ev.org.br/catalogo-de-cursos?query={}", "base": "https://www.ev.org.br", "filter": "/curso/", "type": "free"},
    "Udacity": {"url": "https://www.udacity.com/courses/all?search={}", "base": "https://www.udacity.com", "filter": "/course/", "type": "mixed"},
    "Alison": {"url": "https://alison.com/courses?query={}&category=it", "base": "https://alison.com", "filter": "/course/", "type": "free"},
    "Khan Academy": {"url": "https://www.khanacademy.org/search?page_search_query={}", "base": "https://www.khanacademy.org", "filter": "/x/", "type": "free"},
    "freeCodeCamp": {"url": "https://www.freecodecamp.org/news/search?query={}", "base": "https://www.freecodecamp.org/news", "filter": "/", "type": "free"},
    "Alura": {"url": "https://www.alura.com.br/busca?query={}", "base": "https://www.alura.com.br", "filter": "/curso/", "type": "paid"},
    "DataCamp": {"url": "https://www.datacamp.com/search?q={}", "base": "https://www.datacamp.com", "filter": "/courses/", "type": "paid"},
    "Pluralsight": {"url": "https://www.pluralsight.com/search?q={}", "base": "https://www.pluralsight.com", "filter": "/courses/", "type": "paid"},
    "Class Central": {"url": "https://www.classcentral.com/search?q={}", "base": "https://www.classcentral.com", "filter": "/course/", "type": "mixed"},
}

SITES_PENTEST = {
    "HackerSec": {"url": "https://hackersec.com/cursos-gratuitos/", "base": "https://hackersec.com", "filter": "/curso/", "type": "free"},
    "Cybrary": {"url": "https://www.cybrary.it/catalog/all/", "base": "https://www.cybrary.it", "filter": "/course/", "type": "mixed"},
    "Hack The Box Academy": {"url": "https://academy.hackthebox.com/catalogue", "base": "https://academy.hackthebox.com", "filter": "/module/", "type": "mixed"},
}

MAPA_CATEGORIAS = {
    "programacao": (["programação", "python", "javascript", "java"], "💻 Cursos de Programação"),
    "redes": (["redes de computadores", "ccna", "infraestrutura"], "🌐 Cursos de Redes"),
    "cloud": (["aws", "azure", "google cloud"], "☁️ Cursos de Cloud"),
    "seguranca": (["segurança da informação", "pentest", "hacking etico"], "🛡️ Cursos de Segurança"),
    "dados": (["sql", "banco de dados", "nosql"], "🗄️ Cursos de Banco de Dados"),
    "ciencia_dados": (["ciencia de dados", "machine learning", "ia"], "📊 Cursos de Ciência de Dados"),
    "devops": (["devops", "docker", "kubernetes"], "⚙️ Cursos de DevOps"),
}

# --- CONFIGURAÇÃO DO BOT ---
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# --- BANCO DE DADOS ---
def iniciar_banco_de_dados():
    with sqlite3.connect(DB_FILE) as conexao:
        conexao.execute('''
            CREATE TABLE IF NOT EXISTS inscricoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                course_title TEXT NOT NULL,
                course_url TEXT NOT NULL,
                UNIQUE(user_id, course_url)
            )
        ''')

# --- COMPONENTES DE UI ---
class CursoView(discord.ui.View):
    def __init__(self, course_title: str, course_url: str):
        super().__init__(timeout=None)
        self.course_title = course_title
        self.course_url = course_url

    @discord.ui.button(label="✅ Salvar na minha lista", style=discord.ButtonStyle.success)
    async def inscrever_button_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = interaction.user.id
        try:
            with sqlite3.connect(DB_FILE) as con:
                con.execute(
                    "INSERT INTO inscricoes (user_id, course_title, course_url) VALUES (?, ?, ?)",
                    (user_id, self.course_title, self.course_url)
                )
            await interaction.response.send_message(f"Você salvou o curso: **{self.course_title}**!", ephemeral=True)
        except sqlite3.IntegrityError:
            await interaction.response.send_message("Você já salvou este curso!", ephemeral=True)
        except Exception:
            await interaction.response.send_message("Ocorreu um erro ao salvar o curso.", ephemeral=True)

class CategoriaSelect(discord.ui.Select):
    def __init__(self, course_type: CourseType):
        self.course_type = course_type
        options = [
            discord.SelectOption(label="Programação", emoji="💻", value="programacao"),
            discord.SelectOption(label="Redes", emoji="🌐", value="redes"),
            discord.SelectOption(label="Cloud", emoji="☁️", value="cloud"),
            discord.SelectOption(label="Segurança", emoji="🛡️", value="seguranca"),
            discord.SelectOption(label="Banco de Dados", emoji="🗄️", value="dados"),
            discord.SelectOption(label="Ciência de Dados", emoji="📊", value="ciencia_dados"),
            discord.SelectOption(label="DevOps", emoji="⚙️", value="devops"),
        ]
        super().__init__(placeholder="Escolha uma área de TI para explorar...", options=options)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True, ephemeral=True)
        categoria_key = self.values[0]
        termos, titulo_header_base = MAPA_CATEGORIAS[categoria_key]

        tipo_texto = "Pagos" if self.course_type == "paid" else "Gratuitos"
        titulo_header = f"{titulo_header_base} ({tipo_texto})"

        tasks = []
        if categoria_key == "seguranca":
            tasks.append(pesquisar_cursos_pentest(course_type=self.course_type))

        for termo in termos:
            tasks.append(pesquisar_cursos_online(termo, course_type=self.course_type))

        resultados = await asyncio.gather(*tasks)
        cursos = list(dict.fromkeys([c for sub in resultados for c in sub]))
        await _enviar_resultados_para_discord(interaction, cursos, titulo_header)

class CategoriaTIView(discord.ui.View):
    def __init__(self, course_type: CourseType):
        super().__init__(timeout=None)
        self.add_item(CategoriaSelect(course_type))

# --- FUNÇÕES DE PESQUISA ---
async def _fetch_page(session, url):
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        async with session.get(url, headers=headers, timeout=15) as response:
            return await response.text()
    except Exception:
        return ""

def _parse_courses(html, base_url, filter_keyword):
    cursos = []
    soup = BeautifulSoup(html, "html.parser")
    for a in soup.find_all("a", href=True):
        href = a['href']
        if filter_keyword in href:
            link = href if href.startswith("http") else urllib.parse.urljoin(base_url, href)
            title = a.get_text(strip=True)
            if len(title) < 3:
                continue
            cursos.append((title, link))
    return list(dict.fromkeys(cursos))

async def _scrape_site(session, url_template, base_url, filter_keyword):
    html = await _fetch_page(session, url_template)
    return _parse_courses(html, base_url, filter_keyword) if html else []

async def pesquisar_cursos_online(termo, course_type="all"):
    termo_fmt = urllib.parse.quote_plus(termo)
    sites = {
        k: v for k, v in SITES_DE_BUSCA.items()
        if course_type == "all" or v["type"] == course_type or v["type"] == "mixed"
    }
    async with aiohttp.ClientSession() as session:
        results = await asyncio.gather(*[
            _scrape_site(session, v["url"].format(termo_fmt), v["base"], v["filter"])
            for v in sites.values()
        ])
    return [c for sub in results for c in sub]

async def pesquisar_cursos_pentest(course_type="all"):
    sites = {
        k: v for k, v in SITES_PENTEST.items()
        if course_type == "all" or v["type"] == course_type or v["type"] == "mixed"
    }
    async with aiohttp.ClientSession() as session:
        results = await asyncio.gather(*[
            _scrape_site(session, v["url"], v["base"], v["filter"])
            for v in sites.values()
        ])
    return [c for sub in results for c in sub]

async def _enviar_resultados_para_discord(interaction, cursos, titulo_header):
    if not cursos:
        await interaction.followup.send(f"Nenhum curso encontrado para '{titulo_header}'.", ephemeral=True)
        return

    cursos = cursos[:10]
    lista = "\n".join(f"{i}. **[{c[0][:75]}]({c[1]})**" for i, c in enumerate(cursos, 1))
    embed = discord.Embed(title=titulo_header, description=lista, color=discord.Color.blue())
    embed.set_footer(text=f"Mostrando {len(cursos)} resultados.")
    await interaction.followup.send(embed=embed, ephemeral=True)

    for titulo, url in cursos:
        view = CursoView(titulo, url)
        embed_curso = discord.Embed(title=titulo, url=url, description="Clique abaixo para salvar este curso.", color=discord.Color.blurple())
        await interaction.followup.send(embed=embed_curso, view=view, ephemeral=True)

# --- EVENTOS E COMANDOS ---
@bot.event
async def on_ready():
    print(f"Bot conectado como {bot.user}")
    iniciar_banco_de_dados()
    try:
        synced = await bot.tree.sync()
        print(f"{len(synced)} comandos sincronizados.")
    except Exception as e:
        print(f"Erro ao sincronizar comandos: {e}")

@bot.tree.command(name="cursos_gratuitos", description="Encontre cursos de TI gratuitos.")
async def cursos_gratuitos(interaction):
    await interaction.response.send_message("Escolha uma área:", view=CategoriaTIView("free"), ephemeral=True)

@bot.tree.command(name="cursos_pagos", description="Encontre cursos de TI pagos.")
async def cursos_pagos(interaction):
    await interaction.response.send_message("Escolha uma área:", view=CategoriaTIView("paid"), ephemeral=True)

@bot.tree.command(name="pesquisar_cursos", description="Pesquise cursos por termo.")
@app_commands.describe(termo="O que você quer aprender?")
async def pesquisar_cursos(interaction, termo: str):
    await interaction.response.defer(thinking=True, ephemeral=True)
    resultados = await pesquisar_cursos_online(termo, "all")
    await _enviar_resultados_para_discord(interaction, resultados, f"🔎 Resultados para '{termo}'")

@bot.tree.command(name="meus_cursos", description="Veja seus cursos salvos.")
async def meus_cursos(interaction):
    with sqlite3.connect(DB_FILE) as con:
        cursos = con.execute("SELECT course_title, course_url FROM inscricoes WHERE user_id = ?", (interaction.user.id,)).fetchall()
    if not cursos:
        await interaction.response.send_message("Você ainda não salvou cursos.", ephemeral=True)
        return
    lista = "\n".join(f"{i}. **[{c[0][:70]}]({c[1]})**" for i, c in enumerate(cursos[:25], 1))
    embed = discord.Embed(title="📚 Meus Cursos Salvos", description=lista, color=discord.Color.green())
    await interaction.response.send_message(embed=embed, ephemeral=True)

# --- EXECUÇÃO ---
if not TOKEN:
    print("ERRO: DISCORD_TOKEN não configurado.")
else:
    bot.run(TOKEN)
