import React, { useState } from 'react';
import { useForm, SubmitHandler } from 'react-hook-form';
import { useUserState } from '../state-mgmt/user';
import { useLocation } from 'wouter';
import { useUser } from '../context/UserContext'; // Import UserContext

type LoginFormInputs = {
  username: string;
  password: string;
};

const Login = () => {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormInputs>();
  const [error, setError] = useState<string | null>(null);

  const setUser = useUserState().setData;
  const [, setLocation] = useLocation();
  const { fetchUser } = useUser(); // Access fetchUser from UserContext

  const onSubmit: SubmitHandler<LoginFormInputs> = async (data) => {
    try {
      const response = await fetch('/api/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      });
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Login failed');
      }
      const responseData = await response.json();

      setUser({
        id: responseData.user.id,
        username: responseData.user.username,
        isSignedOn: true,
      });

      // Refetch session data after login
      await fetchUser(); // Update user context with session data
      setError(null);
      setLocation('/');
    } catch (error: unknown) {
      if (error instanceof Error) {
        setError(error.message);
      } else {
        setError('An unexpected error occurred.');
      }
    }
  };

  return (
    <div className='login-container'>
      <form onSubmit={handleSubmit(onSubmit)}>
        <label htmlFor='username'>Username:</label>
        <input
          type='text'
          id='username'
          {...register('username', { required: 'Username is required' })}
        />
        {errors.username && <p className='error'>{errors.username.message}</p>}

        <label htmlFor='password'>Password:</label>
        <input
          type='password'
          id='password'
          {...register('password', { required: 'Password is required' })}
        />
        {errors.password && <p className='error'>{errors.password.message}</p>}

        <button type='submit'>Login</button>
        {error && <p className='error'>{error}</p>}
      </form>
      <div className='google-login'>
        <a href='/api/login-with-google'>Sign in with Google</a>
      </div>
      <div className='signup-link'>
        <a href='/signup'>Create Account</a>
      </div>
    </div>
  );
};

export default Login;
