<!DOCTYPE html>
<html lang="pt-BR">
	<body>
		<div class="container">
			<h1>Centralized Data Engine</h1>
			<img src="https://github.com/bon4to/cde/assets/129971622/e1c1187c-e281-4f2b-8453-42cc4beb6c34" alt="git-cde-banner">
			<p>O projeto CDE é uma plataforma colaborativa desenvolvida com o intuito de facilitar atividades do meio empresarial. Aqui você pode entender a finalidade, funcionalidades principais, uso básico e requisitos do sistema.
			O sistema teve seu primeiro release em janeiro de 2024.</p>
			<h2>Objetivo</h2>
			<p>Com uma abordagem centralizada no usuário, busca-se melhorar a produtividade, bem como a centralização de atividades, promovendo soluções e evolução contínua da plataforma à serviço da empresa.</p>
			<h2>Ferramentas desenvolvidas</h2>
			<ul>
				<li>Endereçamento de Estoque</li>
				<li>Movimentação e Faturamento de Estoque</li>
				<li>Programação de Envase/Processamento</li>
				<li>Ferramentas Específicas: Ferramentas com usos esporádicos ou de menor complexidade lógica.
					<ul>
						<li>Calculadora Automatizada de Rótulos: Calcula uma média de rótulos por rolo.</li>
						<li>Gerador de Etiquetas QR-Code: Gera layout de etiqueta para Bartender.</li>
					</ul>
				</li>
			</ul>
			<h2>Requisitos de Sistema</h2>
			<ul>
				<li>Python 3.12 (64 bits)</li>
				<li>SQLite3 (não é necessária a instalação)</li>
				<li>Suportado em Windows, Linux e MacOS</li>
			</ul>
			<h3>Frameworks e Bibliotecas:</h3>
			<ul>
				<li><a href="https://flask.palletsprojects.com/">Flask</a>: 3.0.2 - Microframework Web em Python.</li>
				<li><a href="https://jinja.palletsprojects.com/">Jinja2</a>: 3.1.3 - Motor de template moderno para Python.</li>
				<li><a href="https://passlib.readthedocs.io/en/stable/">passlib</a>: 1.7.4 - Biblioteca Python para hashing de senhas.</li>
				<li><a href="https://pypi.org/project/qrcode/">qrcode</a>: 7.4.2 - Biblioteca Python para geração de códigos QR.</li>
				<li><a href="https://python-pillow.readthedocs.io/">Pillow</a>: 10.2.0 - Biblioteca Python para processamento de imagens.</li>
				<li><a href="https://docs.python-requests.org/en/latest/">requests</a>: 2.31.0 - Biblioteca HTTP para Python.</li>
				<li><a href="https://werkzeug.palletsprojects.com/">Werkzeug</a>: 3.0.1 - Biblioteca WSGI para Python.</li>
			</ul>
			<h2>Instalação</h2>
			<ol>
				<li>Clone o repositório do projeto:<br>
					<code>git clone https://github.com/bon4to/cde.git</code>
				</li>
				<li>Instale as dependências:<br>
					<code>pip install -r requirements.txt</code>
				</li>
				<li>Execute a aplicação:<br>
					<code>python cde.py</code>
					<br>
					ou (em produção):
					<br>
					<code>python cde_wsgi.py</code>
				</li>
				<li>Acesse a aplicação no navegador:<br>
					<code>http://localhost:5005/</code>
				</li>
			</ol>
			<h2>Uso Básico</h2>
			<ol>
				<li>Faça login na aplicação utilizando as credenciais de administrador.</li>
				<li>Navegue pelas diferentes seções para acessar as funcionalidades disponíveis.</li>
			</ol>
			<h2>Contribuições</h2>
			<p>Contribuições são bem-vindas! Sinta-se à vontade para abrir um problema ou enviar uma solicitação de pull request.</p>
			<h2>Autor</h2>
			<p>Lucas G. Bonato - <a href="mailto:bon4to@icloud.com">bon4to@icloud.com</a> | <a href="https://github.com/bon4to">github.com/bon4to</a></p>
			<h2>Licença</h2>
			<p>Este projeto é licenciado sob a licença MIT. Veja o arquivo <a href="https://github.com/bon4to/cde/blob/main/LICENSE">LICENSE</a> para mais detalhes.</p>
		</div>
	</body>
</html>
