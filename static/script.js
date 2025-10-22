// static/script.js
const sendBtn = document.getElementById('send-btn');
const userInput = document.getElementById('user-input');
const chatBox = document.getElementById('chat-box');
const sessionInput = document.getElementById('session-id');

function addMessage(text, who) {
  const div = document.createElement('div');
  div.className = 'message ' + (who === 'user' ? 'user' : 'bot');
  div.innerText = text;
  chatBox.appendChild(div);
  chatBox.scrollTop = chatBox.scrollHeight;
}

async function sendMessage() {
  const session_id = sessionInput.value || 'default';
  const message = userInput.value.trim();
  if (!message) return;
  addMessage(message, 'user');
  userInput.value = '';

  try {
    const resp = await fetch('/chat', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({session_id, message})
    });
    const data = await resp.json();
    if (data && data.reply) {
      addMessage(data.reply, 'bot');
    } else {
      addMessage("Sorry, something went wrong.", 'bot');
    }
  } catch (err) {
    addMessage("Network error: " + err.message, 'bot');
  }
}

sendBtn.addEventListener('click', sendMessage);
userInput.addEventListener('keydown', (e) => { if (e.key === 'Enter') sendMessage(); });
