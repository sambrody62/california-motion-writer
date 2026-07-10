import React from 'react';

export interface Question {
  id: string;
  type: string;
  label: string;
  required: boolean;
  options?: string[];
  placeholder?: string;
  help_text?: string;
}

interface Props {
  question: Question;
  register: any;
  errors: Record<string, any>;
}

const inputClass =
  'mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 sm:text-sm';

export const QuestionField: React.FC<Props> = ({ question, register, errors }) => {
  switch (question.type) {
    case 'text':
      return (
        <input
          {...register(question.id, { required: question.required })}
          id={question.id}
          type="text"
          className={inputClass}
          placeholder={question.placeholder}
        />
      );

    case 'textarea':
      return (
        <textarea
          {...register(question.id, { required: question.required })}
          id={question.id}
          rows={4}
          className={inputClass}
          placeholder={question.placeholder}
        />
      );

    case 'select':
      return (
        <select
          {...register(question.id, { required: question.required })}
          id={question.id}
          className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm rounded-md"
        >
          <option value="">Choose...</option>
          {question.options?.map((opt) => (
            <option key={opt} value={opt}>{opt}</option>
          ))}
        </select>
      );

    case 'radio':
      return (
        <div className="mt-2 space-y-2">
          {question.options?.map((opt) => (
            <label key={opt} className="inline-flex items-center mr-4">
              <input
                {...register(question.id, { required: question.required })}
                type="radio"
                value={opt}
                className="form-radio h-4 w-4 text-primary-600"
              />
              <span className="ml-2">{opt}</span>
            </label>
          ))}
        </div>
      );

    case 'checkbox':
      return (
        <div className="mt-2 space-y-2">
          {question.options?.map((opt) => (
            <label key={opt} className="flex items-center">
              <input
                {...register(`${question.id}.${opt}`)}
                type="checkbox"
                className="form-checkbox h-4 w-4 text-primary-600"
              />
              <span className="ml-2">{opt}</span>
            </label>
          ))}
        </div>
      );

    case 'date':
      return (
        <input
          {...register(question.id, { required: question.required })}
          id={question.id}
          type="date"
          className={inputClass}
        />
      );

    default:
      return null;
  }
};
