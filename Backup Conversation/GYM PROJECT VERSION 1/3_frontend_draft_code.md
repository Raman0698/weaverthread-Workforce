```html
<!DOCTYPE html>
<html lang="en" class="scroll-smooth">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Weaverthread Gym - Premium User Registration</title>
  <!-- Tailwind CSS CDN -->
  <script src="https://cdn.tailwindcss.com"></script>
  <style>
    /* Custom gradient animations for premium feel */
    .glow-text {
      background: linear-gradient(90deg, #f43f5e, #fb7185, #f43f5e);
      background-size: 200% 200%;
      animation: gradientShift 3s ease infinite;
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }
    @keyframes gradientShift {
      0% {background-position: 0% 50%;}
      50% {background-position: 100% 50%;}
      100% {background-position: 0% 50%;}
    }

    /* Password strength bar transitions */
    #strengthBar {
      transition: width 0.3s ease-in-out;
    }
  </style>
</head>
<body class="bg-gradient-to-b from-gray-900 via-gray-800 to-gray-900 min-h-screen flex items-center justify-center px-4">

  <main class="max-w-lg w-full bg-gray-900 bg-opacity-80 rounded-3xl shadow-2xl p-12 text-gray-100 border border-gray-700 ring-1 ring-gray-600">
    <h1 class="text-4xl font-extrabold text-center mb-6 glow-text select-none">Join Weaverthread Gym</h1>
    <p class="text-center text-gray-400 mb-8">Elevate your fitness journey with us. Register now!</p>

    <form id="registrationForm" novalidate class="space-y-6" autocomplete="off" spellcheck="false">
      <div>
        <label for="fullName" class="block text-sm font-semibold mb-1">Full Name<span class="text-pink-500 ml-1">*</span></label>
        <input
          type="text"
          id="fullName"
          name="fullName"
          minlength="2"
          maxlength="255"
          required
          placeholder="Your full name"
          class="w-full rounded-md border border-gray-700 bg-gray-800 focus:border-pink-500 focus:ring-pink-500 focus:ring-2 px-4 py-3 text-gray-200 text-base placeholder-gray-500 transition"
        />
        <p class="mt-1 text-xs text-red-500 min-h-[1.25rem]" aria-live="polite"></p>
      </div>

      <div>
        <label for="email" class="block text-sm font-semibold mb-1">Email Address<span class="text-pink-500 ml-1">*</span></label>
        <input
          type="email"
          id="email"
          name="email"
          autocomplete="email"
          required
          placeholder="you@example.com"
          class="w-full rounded-md border border-gray-700 bg-gray-800 focus:border-pink-500 focus:ring-pink-500 focus:ring-2 px-4 py-3 text-gray-200 text-base placeholder-gray-500 transition"
        />
        <p class="mt-1 text-xs text-red-500 min-h-[1.25rem]" aria-live="polite"></p>
      </div>

      <div>
        <label for="password" class="block text-sm font-semibold mb-1">Password<span class="text-pink-500 ml-1">*</span></label>
        <input
          type="password"
          id="password"
          name="password"
          autocomplete="new-password"
          required
          minlength="8"
          maxlength="128"
          placeholder="Create a strong password"
          aria-describedby="passwordHelp"
          class="w-full rounded-md border border-gray-700 bg-gray-800 focus:border-pink-500 focus:ring-pink-500 focus:ring-2 px-4 py-3 text-gray-200 text-base placeholder-gray-500 transition"
        />
        <div class="mt-2 h-2 w-full bg-gray-700 rounded-full overflow-hidden" aria-hidden="true">
          <div id="strengthBar" class="h-2 rounded-full bg-pink-600 w-0"></div>
        </div>
        <p id="passwordHelp" class="mt-1 text-xs text-pink-400 font-semibold">Must be 8+ char, with uppercase, lowercase & number</p>
        <p class="mt-1 text-xs text-red-500 min-h-[1.25rem]" aria-live="polite"></p>
      </div>

      <div>
        <label for="phone" class="block text-sm font-semibold mb-1">Phone Number <span class="text-gray-500 italic">(Optional)</span></label>
        <input
          type="tel"
          id="phone"
          name="phone"
          placeholder="+1 (555) 123-4567"
          autocomplete="tel"
          class="w-full rounded-md border border-gray-700 bg-gray-800 focus:border-pink-500 focus:ring-pink-500 focus:ring-2 px-4 py-3 text-gray-200 text-base placeholder-gray-500 transition"
          pattern="^\+?[\d\s\-().]{7,30}$"
        />
        <p class="mt-1 text-xs text-red-500 min-h-[1.25rem]" aria-live="polite"></p>
      </div>

      <div>
        <label for="dob" class="block text-sm font-semibold mb-1">Date of Birth <span class="text-gray-500 italic">(Optional)</span></label>
        <input
          type="date"
          id="dob"
          name="dob"
          max=""
          placeholder="YYYY-MM-DD"
          class="w-full rounded-md border border-gray-700 bg-gray-800 focus:border-pink-500 focus:ring-pink-500 focus:ring-2 px-4 py-3 text-gray-200 text-base placeholder-gray-500 transition"
        />
        <p class="mt-1 text-xs text-red-500 min-h-[1.25rem]" aria-live="polite"></p>
      </div>

      <button
        type="submit"
        class="w-full py-3 bg-gradient-to-r from-pink-600 via-red-500 to-yellow-400 rounded-full text-gray-900 font-extrabold text-lg shadow-lg hover:brightness-110 active:brightness-90 transition"
        aria-live="polite"
      >
        Register Now
      </button>

      <p id="formMessage" role="alert" class="mt-4 text-center font-semibold text-lg min-h-[1.75rem]"></p>
    </form>
  </main>

<script>
  (() => {
    // Elements
    const form = document.getElementById('registrationForm');
    const fullNameInput = form.fullName;
    const emailInput = form.email;
    const passwordInput = form.password;
    const phoneInput = form.phone;
    const dobInput = form.dob;
    const strengthBar = document.getElementById('strengthBar');
    const formMessage = document.getElementById('formMessage');

    // Error message containers (closest p after input)
    const getErrorElem = (input) => input.parentElement.querySelector('p[aria-live]');

    // Set max date on dob to today
    const setDobMaxDate = () => {
      const today = new Date().toISOString().split('T')[0];
      dobInput.setAttribute('max', today);
    };
    setDobMaxDate();

    // Password strength check
    // Returns score 0 to 4
    function checkPasswordStrength(password) {
      let score = 0;
      if (!password) return score;
      // Length >= 8
      if (password.length >= 8) score++;
      // Has lowercase
      if (/[a-z]/.test(password)) score++;
      // Has uppercase
      if (/[A-Z]/.test(password)) score++;
      // Has digit
      if (/\d/.test(password)) score++;
      // Optional: symbols? Not required by spec but adding bonus
      if (/[^A-Za-z0-9]/.test(password)) score++;
      // Cap max score at 4 (because min 8 chars is mandatory)
      return Math.min(score, 4);
    }

    // Update strength bar visually based on score
    function updateStrengthBar(score) {
      // Map score to width percent and color
      // 0 - 0%
      // 1 - 25%
      // 2 - 50%
      // 3 - 75%
      // 4 - 100%
      const widths = [0, 25, 50, 75, 100];
      const colors = [
        'bg-gray-700',
        'bg-red-600',
        'bg-yellow-400',
        'bg-yellow-300',
        'bg-green-400'
      ];
      strengthBar.style.width = widths[score] + '%';
      // Reset classes and add new class
      strengthBar.className = 'h-2 rounded-full ' + colors[score];
    }

    // Email format validation regex (basic)
    function isValidEmail(email) {
      // Using HTML5 validation, but an extra sanity check
      return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
    }

    // Phone format validation (basic international)
    function isValidPhone(phone) {
      if (!phone) return true; // optional
      // Allow +, numbers, spaces, -, (, )
      const re = /^\+?[\d\s\-().]{7,30}$/;
      return re.test(phone);
    }

    // Validate date of birth is in past, optional
    function isValidDob(dob) {
      if (!dob) return true;
      const dobDate = new Date(dob);
      const today = new Date();
      return dobDate <= today;
    }

    // Show error for a specific input
    function showError(input, message) {
      const errorElem = getErrorElem(input);
      if (errorElem) {
        errorElem.textContent = message;
      }
      input.setAttribute('aria-invalid', message ? 'true' : 'false');
    }

    // Clear all errors
    function clearErrors() {
      [fullNameInput, emailInput, passwordInput, phoneInput, dobInput].forEach(input => showError(input, ''));
      formMessage.textContent = '';
      formMessage.className = 'mt-4 text-center font-semibold text-lg min-h-[1.75rem]';
    }

    // Password strength validation according to backend rule:
    // At least 8 chars, at least one uppercase, one lowercase, one number
    function validatePasswordStrength(pw) {
      if (pw.length < 8) return false;
      if (!/[A-Z]/.test(pw)) return false;
      if (!/[a-z]/.test(pw)) return false;
      if (!/\d/.test(pw)) return false;
      return true;
    }

    // Real-time password strength update
    passwordInput.addEventListener('input', () => {
      const score = checkPasswordStrength(passwordInput.value);
      updateStrengthBar(score);
      const pwErrorElem = getErrorElem(passwordInput);
      if (passwordInput.value.length > 0 && !validatePasswordStrength(passwordInput.value)) {
        pwErrorElem.textContent = "Password must have uppercase, lowercase & number.";
        passwordInput.setAttribute('aria-invalid', 'true');
      } else {
        pwErrorElem.textContent = "";
        passwordInput.removeAttribute('aria-invalid');
      }
    });

    // Form submission handler
    form.addEventListener('submit', async e => {
      e.preventDefault();
      clearErrors();

      let isValid = true;

      const fullName = fullNameInput.value.trim();
      const email = emailInput.value.trim().toLowerCase();
      const password = passwordInput.value;
      const phone = phoneInput.value.trim();
      const dob = dobInput.value;

      // Validate Full Name: required, 2-255 chars
      if (!fullName) {
        showError(fullNameInput, "Full name is required.");
        isValid = false;
      } else if (fullName.length < 2) {
        showError(fullNameInput, "Full name must be at least 2 characters.");
        isValid = false;
      }

      // Validate Email: required, format
      if (!email) {
        showError(emailInput, "Email is required.");
        isValid = false;
      } else if (!isValidEmail(email)) {
        showError(emailInput, "Email format is invalid.");
        isValid = false;
      }

      // Validate Password: required, strength
      if (!password) {
        showError(passwordInput, "Password is required.");
        isValid = false;
      } else if (!validatePasswordStrength(password)) {
        showError(passwordInput, "Password does not meet strength requirements.");
        isValid = false;
      }

      // Validate Phone: optional, format
      if (phone && !isValidPhone(phone)) {
        showError(phoneInput, "Phone number format is invalid.");
        isValid = false;
      }

      // Validate DOB: optional, must not be in future
      if (dob && !isValidDob(dob)) {
        showError(dobInput, "Date of birth cannot be in the future.");
        isValid = false;
      }

      if (!isValid) {
        formMessage.textContent = "Please fix the errors above and try again.";
        formMessage.classList.add("text-red-500");
        return;
      }

      // Prepare payload as per API contract
      const payload = {
        full_name: fullName,
        email: email,
        password: password,
      };
      if (phone) payload.phone = phone;
      if (dob) payload.date_of_birth = dob;

      // Disable the submit button and show loading state
      const submitButton = form.querySelector('button[type="submit"]');
      submitButton.disabled = true;
      submitButton.textContent = "Registering...";
      formMessage.textContent = "";

      try {
        const response = await fetch("http://localhost:8000/api/v1/users/register", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(payload),
        });

        if (response.status === 201) {
          const data = await response.json();
          formMessage.textContent = `Welcome aboard, ${data.full_name}! Your account has been created.`;
          formMessage.className = "mt-4 text-center font-bold text-green-400 min-h-[1.75rem]";
          form.reset();
          updateStrengthBar(0);
        } else if (response.status === 409) {
          // Email exists conflict
          showError(emailInput, "An account with this email already exists.");
          formMessage.textContent = "Please use a different email or log in.";
          formMessage.className = "mt-4 text-center font-semibold text-red-500 min-h-[1.75rem]";
        } else if (response.status === 400) {
          // Bad request, extract message if possible
          const errData = await response.json().catch(() => ({}));
          const detail = errData.detail || "Invalid input data.";
          formMessage.textContent = detail;
          formMessage.className = "mt-4 text-center font-semibold text-red-500 min-h-[1.75rem]";
        } else {
          formMessage.textContent = "Unexpected error occurred. Please try again later.";
          formMessage.className = "mt-4 text-center font-semibold text-red-500 min-h-[1.75rem]";
        }
      } catch (error) {
        formMessage.textContent = "Could not connect to the server. Please check your network.";
        formMessage.className = "mt-4 text-center font-semibold text-red-500 min-h-[1.75rem]";
      } finally {
        submitButton.disabled = false;
        submitButton.textContent = "Register Now";
      }
    });

  })();
</script>
</body>
</html>
```
