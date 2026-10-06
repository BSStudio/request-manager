import React from 'react';

type ConditonalWrapperProps = {
  children: React.ReactElement;
  condition: boolean;
  wrapper: (children: React.ReactElement) => React.JSX.Element;
};

const ConditionalWrapper = ({
  children,
  condition,
  wrapper,
}: ConditonalWrapperProps) => (condition ? wrapper(children) : children);

export default ConditionalWrapper;
