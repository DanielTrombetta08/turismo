from crewai.tools import tool
from langchain_tavily import TavilySearch
from langchain_community.tools import DuckDuckGoSearchResults

class SearchTools:
    @tool("Pesquisa na internet")
    def search_tavily(query: str = "") -> str:
        """
        Search the web using Tavily API.
        Recommended for more structured and recent information.
        """
        search_tavily = TavilySearch(max_results=4)
        search_res = search_tavily.invoke(query)
        return search_res

    @tool("Pesquisa na internet com DuckDuckGo")
    def search_duckduckgo(query: str):
        """
        Search the web using DuckDuckGo.
        Returns a list of search results.
        """
        search_tool = DuckDuckGoSearchResults(num_results=4, verbose=True)
        return search_tool.run(query)

class CalculatorTools:
    @tool("Faça um cálculo")
    def calculate(operation):
        """Useful to perform any mathematical calculations,
        like sum, minus, multiplication, division, etc.
        The input to this tool should be a mathematical
        expression, a couple examples are `200*7` or `5000/2*10`
        """
        try:
            return eval(operation)
        except SyntaxError:
            return "Erro: Sintaxe inválida"
