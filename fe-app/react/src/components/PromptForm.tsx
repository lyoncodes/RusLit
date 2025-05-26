// import { useUserState } from '../state-mgmt/user';
import { useForm, SubmitHandler } from 'react-hook-form';
import { FileUploader } from './ui-components';
// import { useQuery } from '@tanstack/react-query';

type PromptFormInputs = {
  prompt: string;
  includeUserBookshelf: boolean;
  files: FileList | null;
};

const PromptForm = () => {
  const { register, handleSubmit, setValue } = useForm<PromptFormInputs>({
    defaultValues: {
      prompt: '',
      includeUserBookshelf: false,
      files: null,
    },
  });
  const handleFilesChange = (files: FileList | null) => {
    setValue('files', files);
  };

  const onSubmit: SubmitHandler<PromptFormInputs> = async (data) => {
    try {
      const response = await fetch('/api/prompt', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      });
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Prompt submission failed');
      }
      const responseData = await response.json();
      console.log(responseData);
    } catch (error) {
      console.error('Error submitting prompt:', error);
    }
  };

  return (
    <div className='prompt-form'>
      <form onSubmit={handleSubmit(onSubmit)}>
        <input
          type='text'
          placeholder='Enter your prompt'
          {...register('prompt', { required: true })}
          className='prompt-input'
        />
        <div>
          <label htmlFor='includeUserBookshelf'>Include User Bookshelf</label>
          <input
            type='checkbox'
            {...register('includeUserBookshelf')}
            className='prompt-checkbox'
          />
        </div>
        <FileUploader onFilesChange={handleFilesChange} />
        <button type='submit' className='prompt-submit'>
          Submit
        </button>
      </form>
    </div>
  );
};
export default PromptForm;
