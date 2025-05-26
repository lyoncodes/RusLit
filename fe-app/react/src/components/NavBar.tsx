import React from 'react';
import { Link } from 'wouter';
import { useUserState } from '../state-mgmt/user';

const NavBar = () => {
  const user = useUserState().data; // Access user state

  return (
    <nav>
      <ul>
        {user?.isSignedOn ? (
          <>
            <li>
              <Link to='/'>Home</Link>
            </li>
            <li>
              <a href='/api/logout'>Logout</a>
            </li>
          </>
        ) : null}
      </ul>
    </nav>
  );
};

export default NavBar;
