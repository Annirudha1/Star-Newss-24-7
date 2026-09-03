document.addEventListener('DOMContentLoaded', function () {
});

// Likes and comments: AJAX handlers
document.addEventListener('DOMContentLoaded', function () {
  function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
      const cookies = document.cookie.split(';');
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.startsWith(name + '=')) {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }

  const csrftoken = getCookie('csrftoken');

  // Like buttons
  document.querySelectorAll('.like-btn').forEach(btn => {
    btn.addEventListener('click', async function () {
      const pk = this.dataset.pk;
      try {
        const resp = await fetch(`/video/${pk}/like/`, {
          method: 'POST',
          headers: {
            'X-CSRFToken': csrftoken,
          },
        });
        if (!resp.ok) throw new Error('Network error');
        const data = await resp.json();
        const countEl = this.querySelector('.like-count');
        if (countEl) countEl.textContent = data.count;
        this.classList.toggle('liked', data.liked);
      } catch (err) {
        console.error('Like failed', err);
      }
    });
  });

  // Comment toggle
  document.querySelectorAll('.comment-toggle').forEach(btn => {
    btn.addEventListener('click', function () {
      const pk = this.dataset.pk;
      const target = document.getElementById('comments-' + pk);
      if (!target) return;
      const isOpen = !target.hasAttribute('hidden');
      if (isOpen) {
        target.setAttribute('hidden', '');
        this.setAttribute('aria-expanded', 'false');
      } else {
        target.removeAttribute('hidden');
        this.setAttribute('aria-expanded', 'true');
      }
    });
  });

  // Comment form submit via AJAX
  document.querySelectorAll('.comment-form').forEach(form => {
    form.addEventListener('submit', async function (e) {
      e.preventDefault();
      const pk = this.dataset.pk;
      const textarea = this.querySelector('textarea[name="content"]');
      if (!textarea) return;
      const content = textarea.value.trim();
      if (!content) return;
      const submitBtn = this.querySelector('.comment-submit');
      if (submitBtn) submitBtn.disabled = true;
      try {
        const formData = new FormData();
        formData.append('content', content);
        const resp = await fetch(`/video/${pk}/comment/`, {
          method: 'POST',
          headers: { 'X-CSRFToken': csrftoken },
          body: formData,
        });
        if (!resp.ok) throw new Error('Network error');
        const data = await resp.json();

        // append comment to list
        const list = document.querySelector('#comments-' + pk + ' .comment-list');
        if (list) {
          const empty = list.querySelector('.empty');
          if (empty) empty.remove();
          const li = document.createElement('li');
          li.className = 'comment-item';
          li.innerHTML = '<strong>' + (data.user || 'You') + '</strong>: ' + data.content;
          list.prepend(li);
        }

        // update comment count
        const toggle = document.querySelector('.comment-toggle[data-pk="' + pk + '"] .comment-count');
        if (toggle) toggle.textContent = data.count;

        textarea.value = '';
      } catch (err) {
        console.error('Comment failed', err);
      } finally {
        if (submitBtn) submitBtn.disabled = false;
      }
    });
  });

});

// Navbar login dropdown toggle
document.addEventListener('DOMContentLoaded', function () {
  const toggle = document.getElementById('nav-login-toggle');
  const panel = document.getElementById('nav-login-panel');
  const menuToggle = document.getElementById('nav-menu-toggle');
  const navMenu = document.getElementById('nav-menu');

  if (menuToggle && navMenu) {
    menuToggle.addEventListener('click', function () {
      const isOpen = navMenu.classList.toggle('open');
      menuToggle.setAttribute('aria-expanded', String(isOpen));
    });
  }

  if (!toggle || !panel) return;

  function closePanel() {
    panel.classList.remove('open');
    panel.setAttribute('aria-hidden', 'true');
    toggle.setAttribute('aria-expanded', 'false');
  }

  function openPanel() {
    panel.classList.add('open');
    panel.setAttribute('aria-hidden', 'false');
    toggle.setAttribute('aria-expanded', 'true');
  }

  toggle.addEventListener('click', function (e) {
    e.stopPropagation();
    if (panel.classList.contains('open')) {
      closePanel();
    } else {
      openPanel();
    }
  });

  // close when clicking outside
  document.addEventListener('click', function (ev) {
    if (!panel.contains(ev.target) && ev.target !== toggle) {
      closePanel();
    }
  });

  // close on escape
  document.addEventListener('keydown', function (ev) {
    if (ev.key === 'Escape') closePanel();
  });
});
