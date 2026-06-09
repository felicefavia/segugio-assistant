import chainlit as cl
import json
from openai import OpenAI
from config import Config
from prompts import query_writer_instrunctions, summarizer_instructions, reflection_instructions
from tavily import TavilyClient

client = OpenAI(base_url=Config.AI_API_URL, api_key=Config.AI_API_KEY)

# Aggiunto 'async' per non bloccare Chainlit
async def llm(developer_prompt, user_prompt, temperature=0, response_format={"type": "json_object"}):
    # Usiamo cl.make_async per eseguire la chiamata sincrona dell'SDK OpenAI in un thread separato
    response = await cl.make_async(client.chat.completions.create)(
        model=Config.LLM_MODEL_LOW,
        messages=[
            {"role": "developer", "content": developer_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=temperature,
        response_format=response_format
    )
    return response.choices[0].message.content

# Aggiunto 'async'
async def optimize_search_query(research_topic):
    formatted_instrunctions = query_writer_instrunctions.format(
        research_topic=research_topic, 
        resarch_topic=research_topic
    )
    # Assicurati che formatted_instrunctions chieda esplicitamente un output JSON
    result = await llm(formatted_instrunctions, "Genera una query per la ricerca web: ")
    obj = json.loads(result)
    return obj

def _format_content(result):
    return f"""
Fonte {result['title']}:\n===\n
URL {result['url']}\n===\n
Contenuto più rilevante: {result['content']}\n===\n
"""

def web_search(search_query):

    tavily_api_key = Config.TAVILY_API_KEY
    max_results = 3
    include_raw = False
    
    client = TavilyClient(api_key=tavily_api_key)
    response = client.search(
        query=search_query,
        max_results=max_results,
        include_raw_content=include_raw
    )

    results = response.get('results', [])
    titles = [result['title'] for result in results]
    contents = [_format_content(result) for result in results]

    return {
        "sources_gathered": titles,
        "web_research_results": contents
    }


async def summarize_sources(web_research_results, research_topic, running_summary=True):
    current_results = "\n".join(web_research_results)

    if running_summary:
        message = (
            f"Estendi questo riassunto: {running_summary}\n\n"
            f"Con questi nuovi riassunti: {current_results} "
            f"Sul tema: {research_topic}"
        )
    else:
        message = (
            f"Genera un riassunto di questi risultati: {current_results} "
            f"Sul tema: {research_topic}"
        )

    output_formatter = None #Vogliamo del testo semplice
    
    # Aggiunto 'await' qui davanti a llm
    return await llm(summarizer_instructions, message, 0.2, output_formatter)


async def reflect_on_summary(resarch_topic, running_summary):
   result = await llm(
        reflection_instructions.format(
            research_topic=resarch_topic, 
            resarch_topic=resarch_topic
        ),
        f"Identifica una lacuna e genera una domanda per la prossima ricerca basandoti su: {running_summary}"
    )
   return json.loads(result)

@cl.on_message
async def main(message: cl.Message):
    user_message = message.content
    
    # Ora usiamo 'await'
    osq = await optimize_search_query(user_message)

    # feed per l'utente
    query, aspect, reason = osq['query'], osq['aspect'], osq['reason']

    await cl.Message(author="system_assistant", content=f"Query di ricerca ottimizzata: \n {query}. \n Mi sono soffermato su questo aspetto: \n {aspect}.\n Per questo motivo: \n {reason}.\n").send()

    running_summary = None
    max_cycles = 2

    while True:
         # Esegui la ricerca sul web
        results = web_search(query)

        titles= "\n".join(results['sources_gathered'])

        await cl.Message(author="system_assistant", content=f"Fonti trovate: {titles}").send()


        summary = await summarize_sources(results['web_research_results'], query, running_summary)

        running_summary = summary

        # Feed utente
        await cl.Message(author="system_assistant", content=f"Riassunto attuale: {summary}").send()


        max_cycles -=1
        if max_cycles <= 0:
            break


        ros = await reflect_on_summary(query, summary)
        query = ros.get('domanda_approfondimento', f"Dimmi di piu su {query}")
        lacuna_conoscenza = ros.get('lacuna_conoscenza', '')

        await cl.Message(author="system_assistant", content=f"Prossima ricerca:\n {query}.\n Mi sono soffermato su questo perchè:\n {lacuna_conoscenza}").send()

    # Fuori dal while
    await cl.Message(
        author="segugio_assistant",
        content=f"Risposta alla tua domanda:\n\n{message.content}\n\nRisposta finale: \n\n {running_summary}"
    ).send()

