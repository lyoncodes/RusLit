import { lazy, Suspense } from 'react';
import { Route, Switch } from 'wouter';

const Home = lazy(() => import('../components/Home'));
const Login = lazy(() => import('../components/Login'));

const AppRouter = () => {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <Switch>
        <Route path='/'>
          <Home />
        </Route>
        <Route path='/login'>
          <Login />
        </Route>
      </Switch>
    </Suspense>
  );
};

export default AppRouter;
