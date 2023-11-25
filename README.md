# Framework - Arbitragem IBOV Futuro 
<br>
Repositório criado como uma base sólida para desenvolvimentos futuros de estratégias envolvendo arbitragem entre IBOV spot e futuro. Cada função possui uma explicação sobre sua utilidade, mas é recomendado entrar no .py em que elas são definidas para sanar potenciais dúvidas.
<br><br>
Alguns pontos centrais:

* dados extraídos com o MetaTrader5
* IBOV calculado em tempo real
* Risk Free para carrego calculado com cotação de DI interpolada entre dois contratos em torno do vencimento do IBOV futuro
* gerenciamento de datas leva em consideração feriados nacionais divulgados em planilha pela Anbima
<br><br>

**Futuros desenvolvimentos:** extrair padrões baseados possivelmente em distâncias anormais em relação ao preço estimado, buscando fornecer liquidez para participantes que precisam/querem comprar independente desse desvio, e assim ser recompensado com o retorno ao preço justo.
