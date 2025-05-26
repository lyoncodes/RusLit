import { createGlobalState } from '.'; // Ensure correct import path

type UserState = {
  id: string;
  username: string;
  isSignedOn: boolean;
  bookList: [];
};

export const useUserState = createGlobalState<UserState>('user', {
  id: '',
  username: '',
  isSignedOn: false,
  bookList: [],
});
