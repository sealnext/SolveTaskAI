# To change Author and Committer
git filter-repo --commit-callback '
if commit.author_name == b"" or commit.author_email == b"" or \
   commit.committer_name == b"" or commit.committer_email == b"":
    commit.author_name = b""
    commit.author_email = b""
    commit.committer_name = b""
    commit.committer_email = b""
' # --force

# To change Commit Message
git filter-repo --message-callback '
import re
return re.sub(br"(?i)andreibade", b"andyblak3", message)
'