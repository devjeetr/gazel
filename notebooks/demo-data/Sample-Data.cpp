public class TrieNode
{
    public TrieNode[] Children;
    public string Word;

    public TrieNode()
    {
        this.Children = new TrieNode[30];
        this.Word = null;
    }
}

public class Trie {
    /** Initialize your data structure here. */
    private TrieNode root;

    public Trie() {
        root = new TrieNode();
    }

    /** Returns if the word is in the trie. */
    public bool Search(string word) {

        TrieNode iter = root;

        foreach (char c in word)
        {
            int cIndex = c - 'a';

            if (iter.Children[cIndex] != null)
            {
                iter = iter.Children[cIndex];
            }
            else {
                return false;
            }
        }

        return iter.Word != null ? true : false;
    }

    /** Inserts a word into the trie. */
    public void Insert(string word) {
        TrieNode iter = root;
        foreach (char c in word)
        {
            int cIndex = c - 'a';

            if (iter.Children[cIndex] == null)
            {
                iter.Children[cIndex] = new TrieNode();
            }

            iter = iter.Children[cIndex];
        }

        iter.Word = word;
    }



    /** Returns if there is any word in the trie that starts with the given prefix. */
    public bool StartsWith(string prefix) {

        TrieNode iter = root;

        foreach (char c in prefix)
        {
            int cIndex = c - 'a';
            if (iter.Children[cIndex] != null)
            {
                iter = iter.Children[cIndex];
            }
            else
            {
                return false;
            }
        }

        return true;
    }
}

/**
 * Your Trie object will be instantiated and called as such:
 * Trie obj = new Trie();
 * obj.Insert(word);
 * bool param_2 = obj.Search(word);
 * bool param_3 = obj.StartsWith(prefix);
 */
