import React from 'react';
import { EvidenceTag, TAG_LABELS, ALL_TAGS } from './evidenceTypes';

interface TagPickerProps {
  selected: EvidenceTag[];
  onChange: (tags: EvidenceTag[]) => void;
}

export const TagPicker: React.FC<TagPickerProps> = ({ selected, onChange }) => {
  const toggle = (tag: EvidenceTag) => {
    if (selected.includes(tag)) {
      onChange(selected.filter((t) => t !== tag));
    } else {
      onChange([...selected, tag]);
    }
  };

  return (
    <fieldset>
      <legend className="block text-sm font-medium text-gray-700 mb-2">
        Category (select all that apply)
      </legend>
      <div className="flex flex-wrap gap-3">
        {ALL_TAGS.map((tag) => (
          <label key={tag} className="flex items-center gap-1.5 cursor-pointer">
            <input
              type="checkbox"
              checked={selected.includes(tag)}
              onChange={() => toggle(tag)}
              aria-label={TAG_LABELS[tag]}
              className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
            />
            <span className="text-sm text-gray-700">{TAG_LABELS[tag]}</span>
          </label>
        ))}
      </div>
    </fieldset>
  );
};
