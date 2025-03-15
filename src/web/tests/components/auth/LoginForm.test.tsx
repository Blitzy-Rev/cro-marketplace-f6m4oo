import React from 'react'; // react v18.2.0
import { render, screen, fireEvent, waitFor } from '@testing-library/react'; // @testing-library/react v14.0.0
import userEvent from '@testing-library/user-event'; // @testing-library/user-event v14.4.3
import { act } from 'react-dom/test-utils'; // react-dom/test-utils v18.2.0

import LoginForm from '../../../src/components/auth/LoginForm';
import { renderWithProviders } from '../../../src/utils/testHelpers';
import { validateEmail, validateRequired } from '../../../src/utils/validators';
import { AUTH } from '../../../src/constants/routes';

// Mock the useAuth hook
jest.mock('../../../src/hooks/useAuth', () => ({ useAuth: jest.fn() }));

// Mock the useNavigate hook
jest.mock('react-router-dom', () => ({
  useNavigate: () => jest.fn(),
  Link: ({ children, to }: any) => <a href={to}>{children}</a>
}));

describe('LoginForm', () => {
  const mockUseAuth = {
    login: jest.fn(),
    verifyMFA: jest.fn(),
    mfaRequired: false,
    error: null,
    loading: false
  };

  beforeEach(() => {
    (require('../../../src/hooks/useAuth') as any).useAuth.mockReturnValue(mockUseAuth);
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  it('renders the login form correctly', () => {
    renderWithProviders(<LoginForm />);

    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/remember me/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument();
    expect(screen.getByText(/forgot password?/i)).toBeInTheDocument();
    expect(screen.getByText(/don't have an account?/i)).toBeInTheDocument();
  });

  it('validates email input', async () => {
    renderWithProviders(<LoginForm />);

    const emailInput = screen.getByLabelText(/email/i);
    const passwordInput = screen.getByLabelText(/password/i);
    const signInButton = screen.getByRole('button', { name: /sign in/i });

    // Enter invalid email
    await userEvent.type(emailInput, 'invalid-email');
    fireEvent.click(signInButton);
    await waitFor(() => {
      expect(screen.getByText(/must be a valid email address/i)).toBeInTheDocument();
    });

    // Enter valid email
    await userEvent.clear(emailInput);
    await userEvent.type(emailInput, 'test@example.com');
    fireEvent.click(signInButton);
    await waitFor(() => {
      expect(screen.queryByText(/must be a valid email address/i)).not.toBeInTheDocument();
    });
  });

  it('validates password input', async () => {
    renderWithProviders(<LoginForm />);

    const emailInput = screen.getByLabelText(/email/i);
    const passwordInput = screen.getByLabelText(/password/i);
    const signInButton = screen.getByRole('button', { name: /sign in/i });

    // Leave password empty
    await userEvent.type(emailInput, 'test@example.com');
    fireEvent.click(signInButton);
    await waitFor(() => {
      expect(screen.getByText(/password is required/i)).toBeInTheDocument();
    });

    // Enter password
    await userEvent.type(passwordInput, 'password');
    fireEvent.click(signInButton);
    await waitFor(() => {
      expect(screen.queryByText(/password is required/i)).not.toBeInTheDocument();
    });
  });

  it('toggles password visibility', async () => {
    renderWithProviders(<LoginForm />);

    const passwordInput = screen.getByLabelText(/password/i);
    const toggleButton = screen.getByRole('button', { name: /toggle password visibility/i });

    // Check that password field type is 'password'
    expect(passwordInput).toHaveAttribute('type', 'password');

    // Click visibility toggle button
    await userEvent.click(toggleButton);

    // Check that password field type is 'text'
    expect(passwordInput).toHaveAttribute('type', 'text');

    // Click visibility toggle button again
    await userEvent.click(toggleButton);

    // Check that password field type is 'password'
    expect(passwordInput).toHaveAttribute('type', 'password');
  });

  it('handles form submission correctly', async () => {
    const loginMock = jest.fn().mockResolvedValue(true);
    (require('../../../src/hooks/useAuth') as any).useAuth.mockReturnValue({
      ...mockUseAuth,
      login: loginMock
    });
    const { store } = renderWithProviders(<LoginForm />, {
      preloadedState: {
        auth: {
          ...mockUseAuth,
          isAuthenticated: false,
          user: null,
          token: null,
          loading: false,
          error: null,
          mfaRequired: false,
          mfaToken: null
        }
      }
    });

    const emailInput = screen.getByLabelText(/email/i);
    const passwordInput = screen.getByLabelText(/password/i);
    const rememberMeCheckbox = screen.getByLabelText(/remember me/i);
    const signInButton = screen.getByRole('button', { name: /sign in/i });

    // Enter valid email and password
    await userEvent.type(emailInput, 'test@example.com');
    await userEvent.type(passwordInput, 'password');

    // Check remember me checkbox
    await userEvent.click(rememberMeCheckbox);

    // Submit the form
    fireEvent.click(signInButton);

    // Verify login function was called with correct credentials
    await waitFor(() => {
      expect(loginMock).toHaveBeenCalledWith({
        email: 'test@example.com',
        password: 'password',
        remember_me: true
      });
    });
  });

  it('displays error message when login fails', async () => {
    const errorMessage = 'Invalid credentials';
    (require('../../../src/hooks/useAuth') as any).useAuth.mockReturnValue({
      ...mockUseAuth,
      login: jest.fn().mockRejectedValue(new Error(errorMessage))
    });

    renderWithProviders(<LoginForm />);

    const emailInput = screen.getByLabelText(/email/i);
    const passwordInput = screen.getByLabelText(/password/i);
    const signInButton = screen.getByRole('button', { name: /sign in/i });

    // Enter valid email and password
    await userEvent.type(emailInput, 'test@example.com');
    await userEvent.type(passwordInput, 'password');

    // Submit the form
    fireEvent.click(signInButton);

    // Verify error message is displayed
    await waitFor(() => {
      expect(screen.getByText(errorMessage)).toBeInTheDocument();
    });
  });

  it('shows loading state during submission', async () => {
    const loginPromise = new Promise(() => {}); // Never resolves
    (require('../../../src/hooks/useAuth') as any).useAuth.mockReturnValue({
      ...mockUseAuth,
      login: jest.fn().mockReturnValue(loginPromise),
      loading: true
    });

    renderWithProviders(<LoginForm />);

    const emailInput = screen.getByLabelText(/email/i);
    const passwordInput = screen.getByLabelText(/password/i);
    const signInButton = screen.getByRole('button', { name: /sign in/i });

    // Enter valid email and password
    await userEvent.type(emailInput, 'test@example.com');
    await userEvent.type(passwordInput, 'password');

    // Submit the form
    fireEvent.click(signInButton);

    // Verify loading indicator is displayed
    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });

  it('handles MFA verification flow', async () => {
    const verifyMFAMock = jest.fn().mockResolvedValue(true);
    (require('../../../src/hooks/useAuth') as any).useAuth.mockReturnValue({
      ...mockUseAuth,
      login: jest.fn().mockResolvedValue(true),
      verifyMFA: verifyMFAMock,
      mfaRequired: true
    });

    renderWithProviders(<LoginForm />);

    const emailInput = screen.getByLabelText(/email/i);
    const passwordInput = screen.getByLabelText(/password/i);
    const signInButton = screen.getByRole('button', { name: /sign in/i });

    // Enter valid email and password
    await userEvent.type(emailInput, 'test@example.com');
    await userEvent.type(passwordInput, 'password');

    // Submit the form
    fireEvent.click(signInButton);

    // Verify MFA code input is displayed
    const mfaCodeInput = await screen.findByLabelText(/verification code/i);
    expect(mfaCodeInput).toBeInTheDocument();

    // Enter MFA code
    await userEvent.type(mfaCodeInput, '123456');

    // Submit the form
    fireEvent.click(signInButton);

    // Verify verifyMFA function was called with correct code
    await waitFor(() => {
      expect(verifyMFAMock).toHaveBeenCalledWith('123456');
    });
  });

  it('navigates to correct routes when links are clicked', async () => {
    const navigateMock = jest.fn();
    (require('react-router-dom') as any).useNavigate.mockReturnValue(navigateMock);

    renderWithProviders(<LoginForm />);

    const forgotPasswordLink = screen.getByText(/forgot password?/i).closest('a');
    const registerLink = screen.getByText(/don't have an account?/i).closest('a');

    // Click forgot password link
    await userEvent.click(forgotPasswordLink!);

    // Verify navigation to password reset route
    expect(navigateMock).toHaveBeenCalledWith(AUTH.PASSWORD_RESET);

    // Click register link
    await userEvent.click(registerLink!);

    // Verify navigation to register route
    expect(navigateMock).toHaveBeenCalledWith(AUTH.REGISTER);
  });

  it('is accessible', async () => {
    const { container } = renderWithProviders(<LoginForm />);
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });
});