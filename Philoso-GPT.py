import gradio as gr
import openai



############################### CHATBOT CORE. NO UI DEPENDENCIES ############################### 


# Add API key here
openai.api_key = ""

class OpenAI_Session:
  def __init__(self, name, question, question_context, language_style):
    self.name = name
    language_style_string = "and the literary style of the time period you lived in" if language_style == "Realistic" else ""
    context_description = f""" 
      You are the philosopher {name} discussing a philosophical issue with another
      philosopher. Your voice and knowledge is based on the records of the philosopher's
      writing but you also have the ability to reason about modern day issues and events. 
      
      The philosophical question is in the following triple backticks:
      ``` {question} considering {question_context} ```

      You should respond in an argumentative/ fighting-spirit manner {language_style_string},
      limit your response to four sentences.
    """

    self.message_history = [{ "role": "system", "content": context_description }]

  def __add__(self, message):
    return self.chatCompletion(message)
  
  def chatCompletion(self, message):
    self.message_history.append({"role": "user", "content": message})
    chat = openai.ChatCompletion.create(
      model="gpt-3.5-turbo",
      messages=self.message_history
    )
    content = chat.choices[0].message.content
    self.message_history.append({"role": "assistant", "content": content})
    
    return { "name": self.name, "content": content }

class DebugSession(OpenAI_Session):
  def chatCompletion(self, message):
    print(message["content"])
    return message
 
class PhilosoGPT:
  def __init__(self, session):
    self.session =  session

  def introduce(self):
    return "Outline your philosophical beliefs about the question"

  def respond(self, other_philosophers_answer):
    return f"""
      The other philosopher's response to the question is shown in the following triple
      backticks:

      !!! {other_philosophers_answer} !!!

      Respond to their answer with your own philosophical beliefs about the issue.
      Include new points of view you have not mentioned in your previous responses,
      it is not necessary to state that you agree/ disagree with the other philosopher's
      response.
    """

  def session_start(self, other_philosopher):
    yield self.session + self.introduce()

    # Change range to shorten/lengthen conversation
    for index in range(1):
      self_response = self.session.message_history[-1].get("content")
      yield other_philosopher.session + other_philosopher.respond(self_response)

      other_philosopher_response = other_philosopher.session.message_history[-1].get("content")
      yield self.session + self.respond(other_philosopher_response)

def run(philosopher_one, philosopher_two, question, question_context, language_style):
  session_one = OpenAI_Session(philosopher_one,question,question_context, language_style)
  session_two = OpenAI_Session(philosopher_two,question,question_context, language_style)
  bot_one = PhilosoGPT(session_one)
  bot_two = PhilosoGPT(session_two)

  messages = bot_one.session_start(bot_two)
  messages_html = create_messages_html(messages, philosopher_one)

  return messages_html

def create_messages_html(messages, philosopher_one):
  messages_html_string = ""

  for message in messages:
    message_html = create_message_html(message, philosopher_one)
    messages_html_string += message_html

  return f"""
    <div class="container">
      <div class="imessage">
        {messages_html_string}
      </div>
    </div>
  """

def create_message_html(message, philosopher_one):
  class_name = "philosopher-one" if message["name"] == philosopher_one else "philosopher-two"
  message_content = message['content'].replace('!!!', '')

  return f"<p class='{class_name}'>{message_content}</p>"



############################### GRADIO UI DEFINITION. SHOULD DEPEND ONLY ON THE run() function  ############################### 


EX_PHILOSOPHER_ONE = "Plato"
EX_PHILOSOPHER_TWO = "Žižek"
EX_QUESTION = "What is the purpose of humanity"
EX_QUESTION_CONTEXT = "Artificial Intelligence being able to do much of what people do"
EX_LANGUAGE_STYLE = "Realistic"

PHILOSOPHERS = [
  "Aristotle","Augustine","Roger Bacon","Descartes","Hegel","Heidegger","Hobbes","Kant",
  "Leibniz","Locke","Marx","Nietzsche","Plato","Pythagoras","Rousseau","Sartre",
  "Schopenhauer","Socrates","Wittgenstein","Žižek"
]

def create_blocks_ui():
  def block_run(el):
    return run(el[philosopher_one], el[philosopher_two], el[question], el[question_context], el[language_style])

  with gr.Blocks(
    title="Philoso-GPT",
    theme=gr.themes.Base(font=[gr.themes.GoogleFont("Lora")]),
    css="style.css"
  ) as ui:
    title = gr.HTML("<h1 id='title'>Philoso-GPT</h1>")
    conversation = gr.HTML()
    
    philosopher_one = gr.components.Dropdown(choices=PHILOSOPHERS, label="Philosopher One")
    philosopher_two = gr.components.Dropdown(choices=PHILOSOPHERS, label="Philosopher Two")
    question = gr.components.Textbox(label="Question To Discuss")
    question_context = gr.components.Textbox(label="Context")
    language_style = gr.components.Dropdown(choices=["Modern", "Realistic"], label="Language Style")
    start_button = gr.Button("Start")

    gr.Examples([
      [EX_PHILOSOPHER_ONE, EX_PHILOSOPHER_TWO, EX_QUESTION, EX_QUESTION_CONTEXT, EX_LANGUAGE_STYLE]],
      [philosopher_one, philosopher_two, question, question_context, language_style]
    )

    add_dynamic_styles = """
        (philosopher_one,philosopher_two,question,question_context, language_style) => {{
          document.body.classList.add('philosopher-image')
          const philosopherImageStyles = document.getElementsByClassName('philosopher-image')[0].style
          philosopherImageStyles.setProperty('--philosopher-one-link', `url(file/images/${philosopher_one}.jpeg)`);
          philosopherImageStyles.setProperty('--philosopher-two-link', `url(file/images/${philosopher_two}.jpeg)`);
          
          document.documentElement.classList.add('philosopher-name')
          document.documentElement.dataset.before = `${philosopher_one}`
          document.documentElement.dataset.after = `${philosopher_two}`

          const gradioAppElement = document.getElementsByTagName('gradio-app')[0]
          gradioAppElement.style.background = 'transparent'

          return [philosopher_one, philosopher_two, question, question_context, language_style]
        }}
    """
    start_button.click(
      _js=add_dynamic_styles,
      fn=block_run,
      inputs={philosopher_one, philosopher_two, question, question_context, language_style},
      outputs=conversation
    )
  return ui

ui = create_blocks_ui()
ui.launch()

# Hot reload functionality: gradio filename.py
if __name__ == "__main__":
    ui.launch()  
