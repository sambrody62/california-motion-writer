import React from 'react';

interface IntakeProgressProps {
  title: string;
  currentStep: number;
  totalSteps: number;
  onStepSelect: (step: number) => void;
}

export const IntakeProgressBar: React.FC<Omit<IntakeProgressProps, 'onStepSelect'>> = ({
  title,
  currentStep,
  totalSteps,
}) => (
  <div className="mb-8">
    <div className="flex items-center justify-between mb-2">
      <h2 className="text-lg font-medium text-gray-900">{title}</h2>
      <span className="text-sm text-gray-500">
        Step {currentStep} of {totalSteps}
      </span>
    </div>
    <div className="w-full bg-gray-200 rounded-full h-2.5">
      <div
        className="bg-primary-600 h-2.5 rounded-full transition-all duration-300"
        style={{ width: `${(currentStep / totalSteps) * 100}%` }}
      ></div>
    </div>
  </div>
);

export const IntakeStepDots: React.FC<Omit<IntakeProgressProps, 'title'>> = ({
  currentStep,
  totalSteps,
  onStepSelect,
}) => (
  <div className="mt-8 flex justify-center space-x-2">
    {Array.from({ length: totalSteps }).map((_, index) => (
      <button
        key={index}
        onClick={() => onStepSelect(index + 1)}
        className={`h-2 w-2 rounded-full ${
          index + 1 === currentStep
            ? 'bg-primary-600'
            : index + 1 < currentStep
            ? 'bg-primary-400'
            : 'bg-gray-300'
        }`}
      />
    ))}
  </div>
);
