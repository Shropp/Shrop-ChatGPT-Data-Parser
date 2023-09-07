from data_tree import ChatDataParser

def main():
    # Start by importing your conversation file.
    parser = ChatDataParser("conversations.json")

    # Use the build_tree function to build trees of certain conversations.
    parser.build_tree("Conversation Title 1", "Conversation Title 2")

    # Alternatively you can use 
    # parser.build_all_trees() 
    # to build all conversations in conversations.json

    # This prints all the paths and titles for nodes that contain a string.
    for node in parser.search_for_string("String to search for"):
        # Prints the node text
        print(node.content)

        # Prints the node path
        print(node.path_and_title()[0], end="\t")
        
        # Prints the conversation title of the node
        print(node.path_and_title()[1], end="\n\n")

    # Printing a full conversation to a file.
    node_to_print = parser.search_for_string("String to search for")[0]
    path, title = node_to_print.path_and_title()

    with open("convo_with_path.txt", "w") as fp:
        fp.write(parser.build_text(title, path))

if __name__ == "__main__":
    main()