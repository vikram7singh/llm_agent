import os
import chainlit as cl
from agents.base_agent import Agent


class ImplementationAgent(Agent):

    tools = [
        {
            "type": "function",
            "function": {
                "name": "udpateMilestone",
                "description": "Implementing or updating the code for that milestone in index.html and style.css. Mark the milestone as done in plan.md by changing '[ ]' to '[x]'.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "cssContent": {
                            "type": "string",
                            "description": "The content to write to the style.css file.",
                        },
                        "htmlContent": {
                            "type": "string",
                            "description": "The content to write to the index.html file.",
                        },
                    },
                    "required": ["cssContent", "htmlContent"],
                    "additionalProperties": False,
                },
            }
        }
    ]
     
    def __init__(self, name, client, prompt="", milestone="", gen_kwargs=None):
        super().__init__(name, client, prompt, gen_kwargs)
        self.milestone = milestone


    async def execute(self, message_history):
        """
        Executes the agent's main functionality.

        Note: probably shouldn't couple this with chainlit, but this is just a prototype.
        """
        copied_message_history = message_history.copy()

        # Check if the first message is a system prompt
        if copied_message_history and copied_message_history[0]["role"] == "system":
            # Replace the system prompt with the agent's prompt
            copied_message_history[0] = {"role": "system", "content": self._build_system_prompt()}
        else:
            # Insert the agent's prompt at the beginning
            copied_message_history.insert(0, {"role": "system", "content": self._build_system_prompt()})

        response_message = cl.Message(content="")
        await response_message.send()

        stream = await self.client.chat.completions.create(messages=copied_message_history, stream=True, tools=self.tools, tool_choice="auto", **self.gen_kwargs)

        function_name = ""
        arguments = ""
        async for part in stream:
            if part.choices[0].delta.tool_calls:
                tool_call = part.choices[0].delta.tool_calls[0]
                function_name_delta = tool_call.function.name or ""
                arguments_delta = tool_call.function.arguments or ""
                
                function_name += function_name_delta
                arguments += arguments_delta
        
            if token := part.choices[0].delta.content or "":
                await response_message.stream_token(token)        
        
        print(":::::::::::::Inside Function Name::::::::::::::", function_name)
        print(":::::::::::::Arguments::::::::::::::", arguments)
        if function_name == "udpateMilestone":
            import json
            
            arguments_dict = json.loads(arguments)
            cssContent = arguments_dict.get("cssContent")
            htmlContent = arguments_dict.get("htmlContent")
            
            if cssContent and htmlContent:
                os.makedirs("artifacts", exist_ok=True)
                with open(os.path.join("artifacts", "style.css"), "w") as file:
                    file.write(cssContent)
                
                with open(os.path.join("artifacts", "index.html"), "w") as file:
                    file.write(htmlContent)
                