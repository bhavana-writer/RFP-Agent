import writer as wf

# This is a placeholder to get you started or refresh your memory.
# Delete it or adapt it as necessary.
# Documentation is available at https://dev.writer.com/framework

# Shows in the log when the app starts
print("Hello world!")

#Workflow configuration
wf.Config.feature_flags = ["workflows"]



# "_my_private_element" won't be serialised or sent to the frontend,
# because it starts with an underscore

initial_state = wf.init_state({
    "my_app": {
        "title": "Hello Writer"
    },
    "_my_private_element": 1337,
    "message": None,
})

