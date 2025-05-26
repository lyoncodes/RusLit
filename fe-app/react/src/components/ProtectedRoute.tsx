import React, { useEffect, useState } from 'react';
import { Redirect } from 'wouter';
import { useUser } from '../context/UserContext';
import { useUserState } from '../state-mgmt/user';

const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const { fetchUser } = useUser();
  const { data: user } = useUserState();
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchSession = async () => {
      await fetchUser();
      setIsLoading(false);
    };
    fetchSession();
  }, [fetchUser]);

  // Wait until the user state is initialized
  if (isLoading) {
    return <p>Loading...</p>;
  }

  // Check if the user is signed on
  if (!user || !user.isSignedOn) {
    return <Redirect to='/login' />;
  }

  return <>{children}</>;
};

export default ProtectedRoute;
