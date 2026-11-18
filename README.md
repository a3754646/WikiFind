# WikiFind
Project Title: WikiFind

Team Members: Ian Livingston (iannl2), Aidan Sosnowski (aidanjs7), Mohamed Kaba (kaba3), Muhammad Rafay Salman(msalman5), SJ Heo (heo11), Shreyas Khati (sskhati2)

Project Coordinator: Ian Livingston (iannl2)

Project Description:

Traditional search engines work best when users already know the correct keyword or name of what they are searching for. However, users often recognize an object or understand what it does without knowing what it is called.

The tool we develop will automatically construct searchable collections and vital articles on Wikipedia to compute their scores and rank candidate entities in order to help users find the key objects that match their defining characteristics. The focus will be on the characteristics of the object or idea instead of its name. For instance, “cooking device with horizontal rods” should return “grill”.

This creates a difficult search problem because the user cannot enter the correct keyword. We will address this problem by allowing users to search using descriptions and characteristics instead of names.

Traditional Wikipedia or search-engine searches are mainly keyword-based. For example, if someone already knows the word “caliper,” they can easily search for it. Our system will retrieve possible objects and rank them based on how well their descriptions match the user's characteristics. Unlike simply asking an LLM for an answer, our system will use an actual information retrieval pipeline, including an inverted index and BM25 ranking, so that results can be traced back to the source documents.

We will use python to collect the selected articles the (MediaWiki API), remove duplicate pages, and clean the article text. We will tokenize and normalize the text, then build an inverted index storing term frequencies and use BM 25 to rank articles based on the user’s description. To evaluate the tool, we will create some descriptive test queries with known correct outputs and measure their accuracy with Mean Reciprocal Rank.

Our work will be fairly distributed among data collection, indexing, BM25 retrieval, evaluation, and interface implementation.
