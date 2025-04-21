import os
import writer as wf
from writerai import Writer

# setting the API key
# i know i shouldn't have to do this twice but i think i might since i'm using the API and writer framework?
wf.api_key = os.getenv("WRITER_API_KEY")
client = Writer( api_key = os.environ.get("WRITER_API_KEY"), )

# SETTING SOME GLOBAL VARIABLES I WILL LIKELY WANT REFERENCED - this is stuff that is true of the overall browser session - i'm only focusing on a browser session with a sloppy ending
# just reading the content locally to start - will eventually come from an upload
# content_brief_text = open("static/parsed-brief.txt", "r").read()
content_brief_text = "to be replaced"
# this is a dict for a ui selection - the dict content is derived from the brief content
list_ui_selection_d_content_brief_text = "this will be a dict for a ui selection..."
# this is the piece of content selected for validation - i disable the componenet after selection so it will not change in the session
selected_content_deliverable = "this will house the selected content"
# the final deliverable content will go here
deliverable_content_final = "the end deliverable content will go here"

# starts with "_", so this function won't be exposed
# don't want LLM callability exposed to the front end
# this function generates the list and also runs a validation to see if the list is ok
def _generate_and_validate_content_list():
    # generator and validator of the output for the user selection list
    # need to make sure the list items aren't too long and that they don't have numbers and i want to sanitize the list a bit
    
    # first LLM API call
    response = client.completions.create (
    model="palmyra-x-003-instruct",
    prompt="the text that follows ': ' is parsed from a brief - this brief requires that pieces of content be generated - please collate the required pieces of content and generate a comma separated list, it is required that list items not be longer than 15 characters, there should be no spaces between the list items: " + content_brief_text,
    )

    response_text = response.choices[0].text

    # sanitizing the string returned since it often comes in with spaces and line breaks etc.
    # .split() with no args splits on any whitespace (spaces, newlines, tabs, etc.)
    response_text = response_text.join(response_text.split())

    #turning it into an array
    list_content_generation_options = response_text.split(',')

    # CHECKS
    # checks to see if string has a number
    check_number_in_string = any(c.isdigit() for c in response_text)
    # checks to see if any strings are over 15 characters long
    check_string_length_in_array = any(len(s) > 15 for s in list_content_generation_options)
    # if there are any TRUE values the output here will be over 0 and invalid and the function needs to be called again
    check_final = check_number_in_string+check_string_length_in_array

    # need to make sure the selection is a JSON object for the Builder UI
    list_content_generation_options = {str(i): v for i, v in enumerate(list_content_generation_options)}

    return {"validation": check_final, "list_user_select": list_content_generation_options}

# starts with "_", so this function won't be exposed
# don't want LLM callability exposed to the front end
# this function generates the requested content deliverable
def _generate_and_validate_content_deliverable ():
    print("okokokoko")

    system_prompt = f"the text that follows ': ' is parsed from a brief - this brief requires that pieces of content be generated - please generate the {selected_content_deliverable} outlined in the brief: "
    
    print("NEW PROMPT FOR CONTENT DELIVERABLE")
    print(system_prompt)

    

    model_fed_prompt = system_prompt + content_brief_text

    print("model is fed here")
    # second LLM API call
    response = client.completions.create (
    model = "palmyra-x-004",
    prompt = model_fed_prompt,
    )

    check_final = 13

    response_text = response.choices[0].text

    return {"validation": check_final, "content": response_text}

# starts with "_", so this function won't be exposed
# don't want LLM callability exposed to the front end
# this function regenerates the requested content deliverable with user input
def _regenerate_content_deliverable_with_user_input (state):
    print("thththt")
    check_final = 13

    new_prompt = f"The chat here was meant to generate a piece of content of the utmost quality. Please regenerate a response such that the user feels confident using this deliverable. The user provided feedback: {state['feedback']}"

    print("NEW CHAT PROMPT")
    print(new_prompt)

    chat = client.chat.chat(
    messages=[
        {
        "content": new_prompt,
        "role": "user",
        },
        {
        "content": f"the text that follows ': ' is parsed from a brief - this brief requires that pieces of content be generated - please generate the {selected_content_deliverable} outlined in the brief: " + content_brief_text,
        "role": "user",
        },
        {
        "content": deliverable_content_final,
        "role": "assistant",
        },
        {
        "content": new_prompt,
        "role": "user",
        },
    ],
    model="palmyra-x-004",
    )

    response_text = chat.choices[0].message.content

    return {"validation": check_final, "content": response_text}


# this thing takes the file, saves it, parses it, and generates a user 
# selection list to decide what piece of content should be generated
# the generated list is generated repeatedly until validation checks pass
def brief_upload_handler(state, payload):
    
    print("BRIEF NAME")
    print(payload[0].get("name"))

    file = client.files.upload (
    content = payload[0].get("data"),
    content_disposition = "attachment; filename=content-brief.pdf",
    content_type="application/pdf"
    )

    print("IF THE UPLOADED THERE WILL BE AN ID BELOW")
    print(file.id)

    response = client.tools.parse_pdf(
    file_id=file.id,
    format="text",
    )
    print(response.content)

    # setting values globally here
    global content_brief_text
    content_brief_text = response.content

    # setting an initial check status - this has to be 0 for validation to pass
    check_content_validation = 1
    # setting the count of generatyions it took to get a workable list
    count_generation = 0
    # now this is a nice little validator function that will run generation until we have a validation of 0 - meaning 0 errors
    # only have 2 checks on the _generate_and_validate_content_list but they works well
    while check_content_validation > 0:
        result_object = _generate_and_validate_content_list()
        print("RESULT OBJECT")
        print (result_object)
        count_generation += 1
        list_user_select = result_object.get("list_user_select")
        check_content_validation = result_object.get("validation")

    
    # setting values globally again here
    global list_ui_selection_o_content_brief_text
    list_ui_selection_o_content_brief_text = list_user_select
    
    # going to disable the upload button to prevent further action there now
    # got a custom "disabled" CSS class
    state["CLASS_file_browser"] = "disabled"
    
    print("THIS TOOK THIS MANY GENERATIONS TO WORK")
    print(count_generation)
    state["display_list_user_select"] = list_user_select

# this thing manages the actual generation of the required content itself
def content_selection_handler(state, payload):
    global selected_content_deliverable
    selected_content_deliverable = list_ui_selection_o_content_brief_text[payload]
    state["CLASS_user_selection"] = "disabled"
    state["display_selected_content_item"] = selected_content_deliverable

    # setting the count of generatyions it took to get a workable list
    count_generation = 0
    # setting an initial check status - this has to be 0 for validation to pass
    check_content_validation = 1
    while check_content_validation < 2:
        result_object = _generate_and_validate_content_deliverable()
        count_generation += 1
        check_content_validation = result_object.get("validation")
        deliverable_content = result_object.get("content")

    global deliverable_content_final
    deliverable_content_final = deliverable_content
        
    state["display_selected_generated_content"] = deliverable_content_final

# this manages the regeneration of the content with required input
def regeneration_handler(state, payload):
    state["CLASS_regeneration"] = "disabled"
    print("th8inging yadayada")
    regenerated_content = _regenerate_content_deliverable_with_user_input(state)

    global deliverable_content_final
    deliverable_content_final = regenerated_content.get("content")

    state["display_selected_generated_content"] = deliverable_content_final


# Initialise the state
initial_state = wf.init_state({
    "my_app": {
        "title": "Content Generator",
    },
    "display_list_user_select": "",
    "display_selected_generated_content": "",
    "display_selected_content_item": "",
    "CLASS_file_browser": "",
    "CLASS_user_selection": "",
    "CLASS_regeneration": "",
})

initial_state.import_stylesheet("theme", "/static/custom.css")
initial_state.import_frontend_module("my_script", "/static/mymodule.js")


    
