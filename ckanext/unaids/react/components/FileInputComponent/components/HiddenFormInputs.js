import React from 'react';

export default function HiddenFormInputs({ hiddenInputs }) {

    return Object.keys(hiddenInputs).map(key => (
        <input
            key={key}
            name={key}
            data-testid={key}
            value={hiddenInputs[key] || ''}
            type="hidden"
        />
    ));

}
