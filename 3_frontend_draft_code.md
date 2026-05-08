```html
<!DOCTYPE html>
<html lang="en" class="bg-gray-50">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Gym Registration System</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="min-h-screen flex items-center justify-center px-4">
    <div class="max-w-md w-full bg-white p-8 rounded-lg shadow-lg">
        <button
            id="btnShowRegister"
            type="button"
            class="mb-6 w-full py-3 px-4 bg-blue-600 hover:bg-blue-700 active:bg-blue-800 text-white font-semibold rounded transition focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-1"
            aria-expanded="false"
            aria-controls="registerForm"
        >
            Show Registration Form
        </button>

        <form id="registerForm" class="space-y-6 hidden" novalidate>
            <div>
                <label for="registerEmail" class="block text-sm font-medium text-gray-700 mb-1">
                    Email Address
                </label>
                <input
                    type="email"
                    id="registerEmail"
                    name="registerEmail"
                    autocomplete="email"
                    required
                    class="w-full rounded border border-gray-300 px-3 py-2 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 invalid:border-red-500"
                    aria-describedby="errorRegisterEmail"
                />
                <p id="errorRegisterEmail" class="mt-1 text-sm text-red-600 invisible" role="alert"></p>
            </div>

            <div>
                <label for="registerUsername" class="block text-sm font-medium text-gray-700 mb-1">
                    Username
                </label>
                <input
                    type="text"
                    id="registerUsername"
                    name="registerUsername"
                    autocomplete="username"
                    required
                    minlength="3"
                    maxlength="20"
                    pattern="^[A-Za-z0-9_]{3,20}$"
                    class="w-full rounded border border-gray-300 px-3 py-2 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 invalid:border-red-500"
                    aria-describedby="errorRegisterUsername"
                />
                <p id="errorRegisterUsername" class="mt-1 text-sm text-red-600 invisible" role="alert"></p>
            </div>

            <div>
                <label for="registerPassword" class="block text-sm font-medium text-gray-700 mb-1">
                    Password
                </label>
                <input
                    type="password"
                    id="registerPassword"
                    name="registerPassword"
                    required
                    minlength="8"
                    autocomplete="new-password"
                    class="w-full rounded border border-gray-300 px-3 py-2 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 invalid:border-red-500"
                    aria-describedby="errorRegisterPassword"
                    spellcheck="false"
                />
                <p id="errorRegisterPassword" class="mt-1 text-sm text-red-600 invisible" role="alert"></p>
            </div>

            <button
                type="submit"
                class="w-full py-3 bg-green-600 hover:bg-green-700 active:bg-green-800 text-white font-semibold rounded transition focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-1"
            >
                Register
            </button>

            <p id="formStatus" class="mt-4 text-center text-sm font-medium" role="alert" aria-live="polite"></p>
        </form>
    </div>

<script>
(() => {
    const btnShowRegister = document.getElementById('btnShowRegister');
    const form = document.getElementById('registerForm');

    // Inputs
    const emailInput = document.getElementById('registerEmail');
    const usernameInput = document.getElementById('registerUsername');
    const passwordInput = document.getElementById('registerPassword');

    // Error message elements
    const emailError = document.getElementById('errorRegisterEmail');
    const usernameError = document.getElementById('errorRegisterUsername');
    const passwordError = document.getElementById('errorRegisterPassword');

    // Form status message element
    const formStatus = document.getElementById('formStatus');

    // Regex patterns for validation
    const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    const usernamePattern = /^[A-Za-z0-9_]{3,20}$/;
    // Password rules: min 8, at least one uppercase, one lowercase, one digit, one special char
    const pwLowercaseRe = /[a-z]/;
    const pwUppercaseRe = /[A-Z]/;
    const pwDigitRe = /\d/;
    const pwSpecialRe = /[^A-Za-z0-9]/;

    // Toggle registration form visibility
    btnShowRegister.addEventListener('click', () => {
        const isHidden = form.classList.contains('hidden');
        if (isHidden) {
            form.classList.remove('hidden');
            btnShowRegister.textContent = 'Hide Registration Form';
            btnShowRegister.setAttribute('aria-expanded', 'true');
            emailInput.focus();
        } else {
            form.classList.add('hidden');
            btnShowRegister.textContent = 'Show Registration Form';
            btnShowRegister.setAttribute('aria-expanded', 'false');
            clearForm();
            clearErrors();
            formStatus.textContent = '';
        }
    });

    // Clear input fields and status messages
    function clearForm() {
        form.reset();
    }

    // Clear all error messages and invalid styles
    function clearErrors() {
        [emailError, usernameError, passwordError].forEach((el) => {
            el.textContent = '';
            el.classList.add('invisible');
        });
        [emailInput, usernameInput, passwordInput].forEach((input) => {
            input.classList.remove('border-red-500');
            input.removeAttribute('aria-invalid');
        });
    }

    // Show error for specific input
    function showError(inputElem, errorElem, message) {
        errorElem.textContent = message;
        errorElem.classList.remove('invisible');
        inputElem.classList.add('border-red-500');
        inputElem.setAttribute('aria-invalid', 'true');
    }

    // Validate each input and return boolean
    function validateEmail() {
        const val = emailInput.value.trim();
        if (val.length === 0) {
            showError(emailInput, emailError, 'Email is required.');
            return false;
        }
        if (!emailPattern.test(val)) {
            showError(emailInput, emailError, 'Please enter a valid email address.');
            return false;
        }
        return true;
    }

    function validateUsername() {
        const val = usernameInput.value.trim();
        if (val.length === 0) {
            showError(usernameInput, usernameError, 'Username is required.');
            return false;
        }
        if (val.length < 3 || val.length > 20) {
            showError(usernameInput, usernameError, 'Username must be between 3 and 20 characters.');
            return false;
        }
        if (!usernamePattern.test(val)) {
            showError(usernameInput, usernameError, 'Username can only contain letters, numbers, and underscores.');
            return false;
        }
        return true;
    }

    function validatePassword() {
        const val = passwordInput.value;
        if (val.length === 0) {
            showError(passwordInput, passwordError, 'Password is required.');
            return false;
        }
        if (val.length < 8) {
            showError(passwordInput, passwordError, 'Password must be at least 8 characters long.');
            return false;
        }
        if (!pwLowercaseRe.test(val)) {
            showError(passwordInput, passwordError, 'Password must contain at least one lowercase letter.');
            return false;
        }
        if (!pwUppercaseRe.test(val)) {
            showError(passwordInput, passwordError, 'Password must contain at least one uppercase letter.');
            return false;
        }
        if (!pwDigitRe.test(val)) {
            showError(passwordInput, passwordError, 'Password must contain at least one digit.');
            return false;
        }
        if (!pwSpecialRe.test(val)) {
            showError(passwordInput, passwordError, 'Password must contain at least one special character.');
            return false;
        }
        return true;
    }

    // Re-validate on input/change and clear errors as user types
    emailInput.addEventListener('input', () => {
        clearErrors();
        validateEmail();
        formStatus.textContent = '';
    });
    usernameInput.addEventListener('input', () => {
        clearErrors();
        validateUsername();
        formStatus.textContent = '';
    });
    passwordInput.addEventListener('input', () => {
        clearErrors();
        validatePassword();
        formStatus.textContent = '';
    });

    // On form submit
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        clearErrors();
        formStatus.textContent = '';
        formStatus.classList.remove('text-red-600', 'text-green-600');

        // Validate all fields
        const emailValid = validateEmail();
        const usernameValid = validateUsername();
        const passwordValid = validatePassword();

        if (!emailValid || !usernameValid || !passwordValid) {
            formStatus.textContent = 'Please fix the errors above and try again.';
            formStatus.classList.add('text-red-600');
            return;
        }

        // Prepare payload
        const payload = {
            email: emailInput.value.trim(),
            username: usernameInput.value.trim(),
            password: passwordInput.value,
        };

        try {
            formStatus.textContent = 'Registering...';
            formStatus.classList.remove('text-red-600');
            formStatus.classList.add('text-gray-700');

            const response = await fetch('/api/register', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(payload),
            });

            const data = await response.json();

            if (response.status === 201) {
                formStatus.textContent = 'User registered successfully! User ID: ' + data.userId;
                formStatus.classList.remove('text-red-600', 'text-gray-700');
                formStatus.classList.add('text-green-600');
                clearForm();
            } else if (response.status === 400) {
                // Show backend error message
                formStatus.textContent = data.error || 'Registration failed due to bad request.';
                formStatus.classList.remove('text-green-600', 'text-gray-700');
                formStatus.classList.add('text-red-600');

                // If error message indicates a specific field, mark inputs as invalid
                if (data.error) {
                    const errText = data.error.toLowerCase();
                    if (errText.includes('email')) {
                        showError(emailInput, emailError, data.error);
                    } else if (errText.includes('username')) {
                        showError(usernameInput, usernameError, data.error);
                    }
                }
            } else {
                formStatus.textContent = 'Unexpected error occurred. Please try again later.';
                formStatus.classList.remove('text-green-600', 'text-gray-700');
                formStatus.classList.add('text-red-600');
            }
        } catch (e) {
            formStatus.textContent = 'Network or server error. Please try again later.';
            formStatus.classList.remove('text-green-600', 'text-gray-700');
            formStatus.classList.add('text-red-600');
        }
    });
})();
</script>
</body>
</html>
```