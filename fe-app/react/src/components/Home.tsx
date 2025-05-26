import { useUserState } from '../state-mgmt/user';
import { useQuery } from '@tanstack/react-query';
import { BookList } from './BookList';
import { Title } from './ui-components';
import PromptForm from './PromptForm';

const fetchUserBooks = async (userId: string | null | undefined) => {
  const response = await fetch(`/api/user/${userId}/books`);
  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }
  return response.json();
};

const Home = () => {
  const user = useUserState().data;

  const { data, isLoading, isError, error } = useQuery(
    ['userBooks', user?.id],
    () => {
      if (!user?.id) {
        return Promise.resolve([]);
      }
      return fetchUserBooks(user.id);
    },
    {
      enabled: !!user?.id,
    }
  );

  if (!user?.username) {
    return (
      <div className='home-container'>
        <h1>Welcome to PyAiMover</h1>
        <p>
          Your one-stop platform for exploring books, managing your profile, and
          discovering personalized recommendations.
        </p>
        <div className='cta'>
          <h2>Get Started</h2>
          <p>
            <a href='/login'>Log in</a> to start your journey.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className='home-container'>
      <Title>RustleLit</Title>
      {isLoading ? (
        <p>Loading user resources...</p>
      ) : isError ? (
        <p>Error fetching user resources: {(error as Error).message}</p>
      ) : data && data.length > 0 ? (
        <>
          <PromptForm />
          <BookList books={data} />
        </>
      ) : null}
    </div>
  );
};

export default Home;
