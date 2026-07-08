import React from 'react';
import { UseFormRegister, FieldValues } from 'react-hook-form';

export interface Question {
  id: string;
  type: string;
  label: string;
  required: boolean;
  options?: string[];
  placeholder?: string;
  help_text?: string;
  condition?: string;
  validation?: any;
}

interface QuestionFieldProps {
  question: Question;
  register: UseFormRegister<FieldValues>;
}

const INPUT_CLASS =
  'mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm';

export const QuestionField: React.FC<QuestionFieldProps> = ({ question, register }) => {
  switch (question.type) {
    case 'text':
      return (
        <input
          {...register(question.id, { required: question.required })}
          id={question.id}
          type="text"
          className={INPUT_CLASS}
          placeholder={question.placeholder}
        />
      );

    case 'textarea':
      return (
        <textarea
          {...register(question.id, { required: question.required })}
          id={question.id}
          rows={4}
          className={INPUT_CLASS}
          placeholder={question.placeholder}
        />
      );

    case 'select':
      return (
        <select
          {...register(question.id, { required: question.required })}
          className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
        >
          <option value="">Choose...</option>
          {question.options?.map(option => (
            <option key={option} value={option}>{option}</option>
          ))}
        </select>
      );

    case 'radio':
      return (
        <div className="mt-2 space-y-2">
          {question.options?.map(option => (
            <label key={option} className="inline-flex items-center mr-4">
              <input
                {...register(question.id, { required: question.required })}
                type="radio"
                value={option}
                className="form-radio h-4 w-4 text-indigo-600"
              />
              <span className="ml-2">{option}</span>
            </label>
          ))}
        </div>
      );

    case 'checkbox':
      return (
        <div className="mt-2 space-y-2">
          {question.options?.map(option => (
            <label key={option} className="flex items-center">
              <input
                {...register(`${question.id}.${option}`)}
                type="checkbox"
                className="form-checkbox h-4 w-4 text-indigo-600"
              />
              <span className="ml-2">{option}</span>
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
          className={INPUT_CLASS}
        />
      );

    case 'time':
      return (
        <input
          {...register(question.id, { required: question.required })}
          id={question.id}
          type="time"
          className={INPUT_CLASS}
        />
      );

    case 'currency':
      return (
        <div className="mt-1 relative rounded-md shadow-sm">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <span className="text-gray-500 sm:text-sm">$</span>
          </div>
          <input
            {...register(question.id, { required: question.required })}
            type="number"
            step="0.01"
            className="pl-7 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
            placeholder="0.00"
          />
        </div>
      );

    default:
      return null;
  }
};
