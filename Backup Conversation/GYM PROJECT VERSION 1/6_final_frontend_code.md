```html
<!DOCTYPE html>
<html lang="en" class="scroll-smooth">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Weaverthread - Posts & Comments</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <style>
    /* For disabled buttons with opacity */
    button:disabled {
      opacity: 0.6;
      cursor: not-allowed;
    }
  </style>
</head>
<body class="bg-gray-50 min-h-screen flex flex-col">

  <header class="bg-blue-600 p-4 text-white flex flex-col sm:flex-row sm:items-center sm:justify-between">
    <h1 class="text-2xl font-bold mb-2 sm:mb-0">Weaverthread</h1>
    <nav class="space-x-2 text-sm sm:text-base">
      <button id="btnShowLogin" class="bg-blue-500 hover:bg-blue-400 px-3 py-1 rounded">Login</button>
      <button id="btnShowRegister" class="bg-blue-500 hover:bg-blue-400 px-3 py-1 rounded">Register</button>
      <button id="btnLogout" class="bg-red-500 hover:bg-red-400 px-3 py-1 rounded hidden">Logout</button>
    </nav>
  </header>

  <main class="flex-grow max-w-5xl mx-auto p-4 w-full">

    <!-- Messages -->
    <div id="messageContainer" class="mb-4"></div>

    <!-- Loading spinner -->
    <div id="loadingIndicator" class="fixed inset-0 bg-black bg-opacity-20 flex items-center justify-center hidden z-50">
      <div class="w-12 h-12 border-4 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
    </div>

    <!-- Authentication forms container -->
    <section id="authSection" class="max-w-md mx-auto p-6 bg-white shadow rounded-lg mb-8">

      <!-- Login form -->
      <form id="loginForm" class="space-y-4" novalidate>
        <h2 class="text-xl font-semibold">Login</h2>
        <div>
          <label for="loginUsername" class="block text-sm font-medium text-gray-700">Username</label>
          <input
            type="text"
            id="loginUsername"
            name="username"
            required
            minlength="3"
            class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:ring-blue-500 focus:border-blue-500"
            autocomplete="username"
          />
        </div>
        <div>
          <label for="loginPassword" class="block text-sm font-medium text-gray-700">Password</label>
          <input
            type="password"
            id="loginPassword"
            name="password"
            required
            minlength="8"
            class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:ring-blue-500 focus:border-blue-500"
            autocomplete="current-password"
          />
        </div>
        <button
          type="submit"
          class="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold p-2 rounded"
        >
          Log In
        </button>
      </form>

      <!-- Register form -->
      <form id="registerForm" class="space-y-4 hidden" novalidate>
        <h2 class="text-xl font-semibold">Register</h2>
        <div>
          <label for="registerEmail" class="block text-sm font-medium text-gray-700">Email</label>
          <input
            type="email"
            id="registerEmail"
            name="email"
            required
            class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:ring-blue-500 focus:border-blue-500"
            autocomplete="email"
          />
        </div>
        <div>
          <label for="registerUsername" class="block text-sm font-medium text-gray-700">Username</label>
          <input
            type="text"
            id="registerUsername"
            name="username"
            required
            minlength="3"
            maxlength="50"
            class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:ring-blue-500 focus:border-blue-500"
            autocomplete="username"
          />
        </div>
        <div>
          <label for="registerPassword" class="block text-sm font-medium text-gray-700">Password</label>
          <input
            type="password"
            id="registerPassword"
            name="password"
            required
            minlength="8"
            class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:ring-blue-500 focus:border-blue-500"
            autocomplete="new-password"
          />
        </div>
        <button
          type="submit"
          class="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold p-2 rounded"
        >
          Register
        </button>
      </form>
    </section>

    <!-- User Profile and Posts Section (hidden if not logged in) -->
    <section id="appSection" class="hidden">

      <!-- User info and new post -->
      <div class="mb-8">
        <h2 class="text-2xl font-semibold mb-4">Welcome, <span id="currentUsername" class="text-blue-600"></span></h2>

        <form id="newPostForm" class="bg-white p-6 rounded-lg shadow space-y-4" novalidate>
          <h3 class="text-xl font-semibold">Create a New Post</h3>
          <div>
            <label for="newPostTitle" class="block text-sm font-medium text-gray-700">Title</label>
            <input type="text" id="newPostTitle" name="title" required minlength="1" maxlength="200"
              class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:ring-blue-500 focus:border-blue-500" />
          </div>
          <div>
            <label for="newPostContent" class="block text-sm font-medium text-gray-700">Content</label>
            <textarea id="newPostContent" name="content" required minlength="1" rows="4"
              class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:ring-blue-500 focus:border-blue-500 resize-y"></textarea>
          </div>
          <button type="submit" class="bg-green-600 hover:bg-green-700 text-white font-semibold px-4 py-2 rounded">
            Post
          </button>
        </form>
      </div>

      <!-- Posts List -->
      <section>
        <h3 class="text-xl font-semibold mb-4">Posts</h3>
        <div id="postsContainer" class="space-y-6">
          <!-- Posts will be appended here -->
        </div>
      </section>

    </section>
  </main>

  <footer class="bg-gray-200 text-center p-4 text-sm text-gray-600">
    &copy; 2024 Weaverthread. All rights reserved.
  </footer>

<script>
(() => {
  // API base URL
  const API_BASE = 'http://localhost:8000/api/v1';

  // Elements
  const messageContainer = document.getElementById('messageContainer');
  const loadingIndicator = document.getElementById('loadingIndicator');
  const loginForm = document.getElementById('loginForm');
  const registerForm = document.getElementById('registerForm');
  const authSection = document.getElementById('authSection');
  const appSection = document.getElementById('appSection');
  const currentUsernameSpan = document.getElementById('currentUsername');
  const postsContainer = document.getElementById('postsContainer');
  const newPostForm = document.getElementById('newPostForm');

  const btnShowLogin = document.getElementById('btnShowLogin');
  const btnShowRegister = document.getElementById('btnShowRegister');
  const btnLogout = document.getElementById('btnLogout');

  // Auth token storage key
  const TOKEN_KEY = 'weaverthread_token';

  // State
  let authToken = null;
  let currentUser = null;
  let posts = [];

  // Utility - show message
  // type: 'error' | 'success' | 'info'
  function showMessage(message, type='info', timeout=5000) {
    messageContainer.innerHTML = '';
    const div = document.createElement('div');
    let bgClass = 'bg-blue-100 text-blue-800 border-blue-300';
    if(type === 'error') bgClass = 'bg-red-100 text-red-800 border-red-300';
    else if(type === 'success') bgClass = 'bg-green-100 text-green-800 border-green-300';

    div.className = `border px-4 py-3 rounded relative mb-2 ${bgClass}`;
    div.role = 'alert';
    div.textContent = message;
    messageContainer.appendChild(div);

    if(timeout > 0) {
      setTimeout(() => {
        if(messageContainer.contains(div)) messageContainer.removeChild(div);
      }, timeout);
    }
  }

  // Show loading spinner
  function showLoading() {
    loadingIndicator.classList.remove('hidden');
  }
  // Hide loading spinner
  function hideLoading() {
    loadingIndicator.classList.add('hidden');
  }

  // Save token
  function saveToken(token) {
    authToken = token;
    localStorage.setItem(TOKEN_KEY, token);
  }

  // Load token
  function loadToken() {
    const token = localStorage.getItem(TOKEN_KEY);
    if(token) {
      authToken = token;
    }
  }

  // Clear token (logout)
  function clearToken() {
    authToken = null;
    localStorage.removeItem(TOKEN_KEY);
  }

  // Fetch helper with error handling and loading
  async function apiFetch(endpoint, options = {}) {
    const url = API_BASE + endpoint;
    let opts = {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...(options.headers || {})
      },
      credentials: 'include', // Keep cookies if any in future
    };
    if(authToken) {
      opts.headers['Authorization'] = `Bearer ${authToken}`;
    }
    showLoading();
    try {
      const response = await fetch(url, opts);
      let data = null;
      if(response.status !== 204) {
        // Try parse JSON if not no-content
        try {
          data = await response.json();
        } catch(e) {
          // Not JSON response
          data = null;
        }
      }
      if(!response.ok) {
        const errMsg = data?.detail || data?.message || response.statusText || "API error";
        throw new Error(errMsg);
      }
      return data;
    } catch (error) {
      throw error;
    } finally {
      hideLoading();
    }
  }

  // Toggle auth forms
  function showLoginForm() {
    loginForm.classList.remove('hidden');
    registerForm.classList.add('hidden');
    btnShowLogin.disabled = true;
    btnShowRegister.disabled = false;
  }
  function showRegisterForm() {
    registerForm.classList.remove('hidden');
    loginForm.classList.add('hidden');
    btnShowLogin.disabled = false;
    btnShowRegister.disabled = true;
  }

  // Initialize form toggle buttons state
  function initAuthToggleButtons() {
    btnShowLogin.disabled = false;
    btnShowRegister.disabled = false;
  }

  // Show/hide login/logout buttons depending on auth state
  function updateUIForAuth() {
    if(authToken && currentUser) {
      authSection.classList.add('hidden');
      appSection.classList.remove('hidden');
      currentUsernameSpan.textContent = currentUser.username;
      btnLogout.classList.remove('hidden');
      btnShowLogin.classList.add('hidden');
      btnShowRegister.classList.add('hidden');
    } else {
      authSection.classList.remove('hidden');
      appSection.classList.add('hidden');
      currentUsernameSpan.textContent = '';
      btnLogout.classList.add('hidden');
      btnShowLogin.classList.remove('hidden');
      btnShowRegister.classList.remove('hidden');
      initAuthToggleButtons();
      showLoginForm();
    }
  }

  // Format datetime string to readable
  function formatDateTime(dateStr) {
    const dt = new Date(dateStr);
    return dt.toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' });
  }

  // Render posts list
  function renderPosts() {
    postsContainer.innerHTML = '';
    if(posts.length === 0) {
      const noPostsDiv = document.createElement('div');
      noPostsDiv.className = 'text-gray-600 italic';
      noPostsDiv.textContent = "No posts available.";
      postsContainer.appendChild(noPostsDiv);
      return;
    }
    for(const post of posts) {
      const postCard = createPostCard(post);
      postsContainer.appendChild(postCard);
    }
  }

  // Create post DOM element with comments and controls
  function createPostCard(post) {
    const card = document.createElement('article');
    card.className = 'bg-white p-4 rounded shadow';

    // Title and meta
    const header = document.createElement('header');
    header.className = 'mb-2 flex justify-between items-center';
    const title = document.createElement('h4');
    title.className = 'text-lg font-semibold text-blue-700 flex-1';
    title.textContent = post.title;
    header.appendChild(title);

    // Edit/Delete buttons if author
    if(currentUser && currentUser.id === post.author_id) {
      const controls = document.createElement('div');
      controls.className = 'flex space-x-2';

      // Edit button
      const btnEdit = document.createElement('button');
      btnEdit.type = 'button';
      btnEdit.className = 'text-yellow-600 hover:text-yellow-800 text-sm font-semibold';
      btnEdit.textContent = 'Edit';
      btnEdit.addEventListener('click', () => openEditPostForm(post, card));
      controls.appendChild(btnEdit);

      // Delete button
      const btnDelete = document.createElement('button');
      btnDelete.type = 'button';
      btnDelete.className = 'text-red-600 hover:text-red-800 text-sm font-semibold';
      btnDelete.textContent = 'Delete';
      btnDelete.addEventListener('click', () => deletePost(post.id));
      controls.appendChild(btnDelete);

      header.appendChild(controls);
    }

    card.appendChild(header);

    // Author & date line
    const meta = document.createElement('p');
    meta.className = 'text-sm text-gray-500 mb-2';
    meta.textContent = `By ${post.author_id === currentUser?.id ? 'You' : 'User #' + post.author_id} on ${formatDateTime(post.created_at)}`;
    card.appendChild(meta);

    // Content paragraph (editable if editing)
    const contentP = document.createElement('p');
    contentP.className = 'mb-4 whitespace-pre-wrap';
    contentP.textContent = post.content;
    contentP.setAttribute('data-content', 'true');
    card.appendChild(contentP);

    // Comments Section
    const commentsSection = document.createElement('section');
    commentsSection.className = 'border-t border-gray-200 pt-3';

    // Comments title
    const commentsTitle = document.createElement('h5');
    commentsTitle.className = 'text-sm font-semibold mb-2 text-gray-700';
    commentsTitle.textContent = 'Comments';
    commentsSection.appendChild(commentsTitle);

    // Comments list container
    const commentsList = document.createElement('div');
    commentsList.className = 'space-y-2 mb-3';
    commentsList.setAttribute('data-comments-list', '');
    commentsSection.appendChild(commentsList);

    // Load comments button or directly load comments
    loadComments(post.id, commentsList);

    // New comment form
    const commentForm = document.createElement('form');
    commentForm.className = 'flex space-x-2';
    commentForm.setAttribute('data-comment-form', '');
    commentForm.addEventListener('submit', async e => {
      e.preventDefault();
      const textarea = commentForm.querySelector('textarea');
      const content = textarea.value.trim();
      if(!content) {
        showMessage("Comment cannot be empty", "error");
        return;
      }
      commentForm.querySelector('button[type="submit"]').disabled = true;
      try {
        await createComment(post.id, content);
        textarea.value = '';
        await loadComments(post.id, commentsList); // Refresh comments list
      } catch(err) {
        showMessage('Failed to post comment: ' + err.message, 'error');
      } finally {
        commentForm.querySelector('button[type="submit"]').disabled = false;
      }
    });

    const commentInput = document.createElement('textarea');
    commentInput.rows = 1;
    commentInput.placeholder = 'Write a comment...';
    commentInput.required = true;
    commentInput.className = 'flex-grow rounded-md border-gray-300 focus:ring-blue-500 focus:border-blue-500 resize-y p-1';
    commentForm.appendChild(commentInput);

    const commentSubmit = document.createElement('button');
    commentSubmit.type = 'submit';
    commentSubmit.textContent = 'Post';
    commentSubmit.className = 'bg-blue-600 hover:bg-blue-700 text-white px-3 rounded disabled:opacity-60';
    commentForm.appendChild(commentSubmit);

    // Only allow commenting if logged in
    if(!authToken) {
      commentForm.style.display = 'none';
    }
    commentsSection.appendChild(commentForm);

    card.appendChild(commentsSection);

    return card;
  }

  // Open an inline post edit form
  function openEditPostForm(post, postCard) {
    const contentP = postCard.querySelector('[data-content]');
    const oldContent = contentP.textContent;

    // Prevent multiple edits
    if(postCard.querySelector('textarea[data-editing]')) return;

    const textarea = document.createElement('textarea');
    textarea.value = post.content;
    textarea.className = 'w-full p-2 border rounded-md focus:ring-blue-500 focus:border-blue-500';
    textarea.setAttribute('data-editing', '');

    // Title editing area
    const header = postCard.querySelector('header h4');
    const oldTitle = header.textContent;
    const titleInput = document.createElement('input');
    titleInput.type = 'text';
    titleInput.value = post.title;
    titleInput.className = 'w-full text-lg font-semibold border rounded-md p-1 mb-2 focus:ring-blue-500 focus:border-blue-500';

    // Replace title text with input
    header.textContent = '';
    header.appendChild(titleInput);

    // Replace content paragraph with textarea
    contentP.replaceWith(textarea);

    // Controls for Save / Cancel
    const controlsDiv = document.createElement('div');
    controlsDiv.className = 'flex space-x-2 mt-2';

    const btnSave = document.createElement('button');
    btnSave.type = 'button';
    btnSave.textContent = 'Save';
    btnSave.className = 'bg-green-600 hover:bg-green-700 text-white px-3 py-1 rounded disabled:opacity-60';
    btnSave.disabled = true;

    const btnCancel = document.createElement('button');
    btnCancel.type = 'button';
    btnCancel.textContent = 'Cancel';
    btnCancel.className = 'bg-gray-400 hover:bg-gray-500 text-white px-3 py-1 rounded';

    controlsDiv.appendChild(btnSave);
    controlsDiv.appendChild(btnCancel);

    postCard.appendChild(controlsDiv);

    // Input validation to enable Save button
    function validateInputs() {
      btnSave.disabled = !titleInput.value.trim() || !textarea.value.trim();
    }
    titleInput.addEventListener('input', validateInputs);
    textarea.addEventListener('input', validateInputs);
    validateInputs();

    btnCancel.addEventListener('click', () => {
      // Restore original title and content
      header.textContent = oldTitle;
      textarea.replaceWith(contentP);
      controlsDiv.remove();
    });

    btnSave.addEventListener('click', async () => {
      btnSave.disabled = true;
      btnCancel.disabled = true;
      try {
        const updatedPost = {
          title: titleInput.value.trim(),
          content: textarea.value.trim()
        };
        await updatePost(post.id, updatedPost);
        post.title = updatedPost.title;
        post.content = updatedPost.content;
        // Update UI
        header.textContent = updatedPost.title;
        contentP.textContent = updatedPost.content;
        textarea.replaceWith(contentP);
        controlsDiv.remove();
        showMessage('Post updated successfully', 'success');
      } catch(err) {
        showMessage('Failed to update post: ' + err.message, 'error');
        btnSave.disabled = false;
        btnCancel.disabled = false;
      }
    });
  }

  // Fetch posts from server
  async function fetchPosts() {
    try {
      const data = await apiFetch('/posts');
      posts = data || [];
      renderPosts();
    } catch(err) {
      showMessage('Failed to load posts: ' + err.message, 'error');
    }
  }

  // Create post API call
  async function createPost(post) {
    return await apiFetch('/posts', {
      method: 'POST',
      body: JSON.stringify(post)
    });
  }

  // Update post API call
  async function updatePost(postId, updatedPost) {
    return await apiFetch('/posts/' + postId, {
      method: 'PUT',
      body: JSON.stringify(updatedPost)
    });
  }

  // Delete post API call
  async function deletePost(postId) {
    if(!confirm('Are you sure you want to delete this post? This action cannot be undone.')) return;
    try {
      showLoading();
      const res = await fetch(API_BASE + '/posts/' + postId, {
        method: 'DELETE',
        headers: {
          'Authorization': 'Bearer ' + authToken,
        },
        credentials: 'include'
      });
      if(!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || res.statusText || 'Failed to delete post');
      }
      // Remove post from local state
      posts = posts.filter(p => p.id !== postId);
      renderPosts();
      showMessage('Post deleted', 'success');
    } catch(err) {
      showMessage('Error deleting post: ' + err.message, 'error');
    } finally {
      hideLoading();
    }
  }

  // Load comments for a post
  async function loadComments(postId, commentsListElem) {
    commentsListElem.innerHTML = '';
    if(!postsContainer.contains(commentsListElem)) return; // If removed from DOM - stop
    try {
      const comments = await apiFetch(`/posts/${postId}/comments`);
      if(comments.length === 0) {
        const emptyDiv = document.createElement('div');
        emptyDiv.className = 'text-sm text-gray-400 italic';
        emptyDiv.textContent = "No comments yet.";
        commentsListElem.appendChild(emptyDiv);
        return;
      }
      for(const comment of comments) {
        const commentElem = createCommentElem(comment);
        commentsListElem.appendChild(commentElem);
      }
    } catch(err) {
      showMessage('Failed to load comments: ' + err.message, 'error');
      commentsListElem.innerHTML = '';
    }
  }

  // Create comment DOM
  function createCommentElem(comment) {
    const div = document.createElement('div');
    div.className = 'bg-gray-100 rounded p-2 relative';
    const contentP = document.createElement('p');
    contentP.className = 'whitespace-pre-wrap';
    contentP.textContent = comment.content;
    div.appendChild(contentP);

    const meta = document.createElement('div');
    meta.className = 'text-xs text-gray-500 flex justify-between items-center mt-1';

    const authorSpan = document.createElement('span');
    authorSpan.textContent = comment.author_id === currentUser?.id ? 'You' : 'User #' + comment.author_id;

    const dateSpan = document.createElement('span');
    dateSpan.textContent = formatDateTime(comment.created_at);

    meta.appendChild(authorSpan);
    meta.appendChild(dateSpan);

    div.appendChild(meta);

    // Delete button if author
    if(currentUser && currentUser.id === comment.author_id) {
      const btnDel = document.createElement('button');
      btnDel.type = 'button';
      btnDel.textContent = 'Delete';
      btnDel.className = 'absolute top-1 right-2 text-red-600 hover:text-red-800 text-xs font-semibold';
      btnDel.addEventListener('click', () => deleteComment(comment.id, div));
      div.appendChild(btnDel);
    }

    return div;
  }

  // Create comment API call
  async function createComment(postId, content) {
    return await apiFetch(`/posts/${postId}/comments`, {
      method: 'POST',
      body: JSON.stringify({ content })
    });
  }

  // Delete comment API call
  async function deleteComment(commentId, elemToRemove) {
    if(!confirm('Delete this comment?')) return;
    try {
      showLoading();
      const res = await fetch(API_BASE + '/comments/' + commentId, {
        method: 'DELETE',
        headers: {
          'Authorization': 'Bearer ' + authToken,
        },
        credentials: 'include'
      });
      if(!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || res.statusText || 'Failed to delete comment');
      }
      elemToRemove.remove();
      showMessage('Comment deleted', 'success');
    } catch(err) {
      showMessage('Error deleting comment: ' + err.message, 'error');
    } finally {
      hideLoading();
    }
  }

  // Fetch and set current user profile
  async function fetchCurrentUser() {
    if(!authToken) return null;
    try {
      const data = await apiFetch('/users/me');
      return data;
    } catch {
      // Token might be invalid/expired: remove token & logout
      clearToken();
      updateUIForAuth();
      return null;
    }
  }

  // Login form submission handler
  loginForm.addEventListener('submit', async e => {
    e.preventDefault();
    const username = loginForm.username.value.trim();
    const password = loginForm.password.value;
    if(!username || !password) {
      showMessage('Please fill in all login fields.', 'error');
      return;
    }
    try {
      const data = await apiFetch('/token', {
        method: 'POST',
        body: new URLSearchParams({
          username,
          password,
        }),
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded'
        }
      });
      saveToken(data.access_token);
      currentUser = await fetchCurrentUser();
      showMessage('Login successful', 'success');
      loginForm.reset();
      updateUIForAuth();
      await fetchPosts();
    } catch(err) {
      showMessage('Login failed: ' + err.message, 'error');
    }
  });

  // Register form submission handler
  registerForm.addEventListener('submit', async e => {
    e.preventDefault();
    const email = registerForm.email.value.trim();
    const username = registerForm.username.value.trim();
    const password = registerForm.password.value;
    if(!email || !username || !password) {
      showMessage('Please fill in all register fields.', 'error');
      return;
    }
    try {
      const newUser = await apiFetch('/users', {
        method: 'POST',
        body: JSON.stringify({ email, username, password })
      });
      showMessage('Registration successful! Please log in.', 'success');
      registerForm.reset();
      showLoginForm();
    } catch(err) {
      showMessage('Registration failed: ' + err.message, 'error');
    }
  });

  // New post form submission
  newPostForm.addEventListener('submit', async e => {
    e.preventDefault();
    const title = newPostForm.title.value.trim();
    const content = newPostForm.content.value.trim();
    if(!title || !content) {
      showMessage('Both title and content are required to create a post.', 'error');
      return;
    }
    newPostForm.querySelector('button[type="submit"]').disabled = true;
    try {
      const createdPost = await createPost({ title, content });
      posts.unshift(createdPost);
      renderPosts();
      newPostForm.reset();
      showMessage('Post created successfully', 'success');
    } catch(err) {
      showMessage('Failed to create post: ' + err.message, 'error');
    } finally {
      newPostForm.querySelector('button[type="submit"]').disabled = false;
    }
  });

  // Logout button handler
  btnLogout.addEventListener('click', () => {
    if(confirm('Are you sure you want to log out?')) {
      clearToken();
      currentUser = null;
      posts = [];
      renderPosts();
      updateUIForAuth();
      showMessage('Logged out', 'info');
    }
  });

  // Toggle auth forms buttons
  btnShowLogin.addEventListener('click', () => {
    showLoginForm();
  });
  btnShowRegister.addEventListener('click', () => {
    showRegisterForm();
  });

  // Initialize app
  async function init() {
    loadToken();
    if(authToken) {
      currentUser = await fetchCurrentUser();
      if(currentUser) {
        await fetchPosts();
      }
    }
    updateUIForAuth();
  }

  // Kick off app load
  init();

})();
</script>
</body>
</html>
```
