import { forwardRef, useEffect, useState } from 'react';

import { useMutation, useQueryClient } from '@tanstack/react-query';
import type { QueryExecuteOptions } from '@tanstack/react-query';
import { isAxiosError } from 'axios';
import { Button } from 'primereact/button';
import { ConfirmPopup } from 'primereact/confirmpopup';
import { Dialog } from 'primereact/dialog';
import type { DialogProps } from 'primereact/dialog';
import { Dropdown } from 'primereact/dropdown';
import { InputTextarea } from 'primereact/inputtextarea';
import { Message } from 'primereact/message';
import { ProgressSpinner } from 'primereact/progressspinner';
import { Controller, useForm } from 'react-hook-form';

import { StatusEnum, TodoAdminListRetrieve } from 'api/models';
import {
  requestTodoCreateMutation,
  requestVideoTodoCreateMutation,
  todoUpdateMutation,
} from 'api/mutations';
import { todoRetrieveQuery } from 'api/queries';
import { queryKeys } from 'api/queryKeys';
import AutoCompleteStaffMultiple from 'components/AutoCompleteStaff/AutoCompleteStaffMultiple';
import { TodoStatusTag } from 'components/StatusTag/StatusTag';
import { getErrorMessage } from 'helpers/ErrorMessageProvider';

interface TodoDialogCreateProps extends DialogProps {
  todoId: number;
}

interface TodoDialogUpdateProps extends DialogProps {
  requestId: number;
  videoId?: number;
}

interface ITodo extends Omit<
  TodoAdminListRetrieve,
  'created' | 'creator' | 'id' | 'request' | 'video'
> {}

const TodoDialog = forwardRef<
  React.Ref<HTMLDivElement>,
  TodoDialogCreateProps & TodoDialogUpdateProps
>(({ onHide, requestId, todoId, videoId, visible, ...props }, ref) => {
  const queryClient = useQueryClient();

  const [loading, setLoading] = useState<boolean>(false);

  const {
    control,
    formState: { isDirty },
    handleSubmit,
    reset,
    setError,
  } = useForm<ITodo>({
    shouldFocusError: false,
  });
  const { mutateAsync } = useMutation(
    todoId
      ? todoUpdateMutation(todoId)
      : videoId
        ? requestVideoTodoCreateMutation(requestId, videoId)
        : requestTodoCreateMutation(requestId),
  );

  useEffect(() => {
    let query: QueryExecuteOptions<TodoAdminListRetrieve> | undefined =
      undefined;

    if (visible) {
      const defaultValues: ITodo = {
        assignees: [],
        description: '',
        status: 1,
      };
      reset({ ...defaultValues });

      if (todoId) {
        setLoading(true);
        query = todoRetrieveQuery(todoId);

        queryClient
          .query(query)
          .then((data) => {
            setLoading(false);
            reset({ ...data });
          })
          .catch(console.error);
      }

      return () => {
        if (query) {
          queryClient
            .cancelQueries({ queryKey: query.queryKey })
            .catch(console.error);
        }
      };
    }
  }, [queryClient, reset, todoId, visible]);

  const onSubmit = async (data: ITodo) => {
    const invalidateQueries = async () => {
      await queryClient.invalidateQueries({
        queryKey: queryKeys.todos(),
      });

      if (requestId) {
        await queryClient.invalidateQueries({
          queryKey: queryKeys.requestTodos(requestId),
        });
      }

      if (videoId) {
        await queryClient.invalidateQueries({
          queryKey: queryKeys.videoTodos(requestId, videoId),
        });
      }
    };

    setLoading(true);

    await mutateAsync({
      ...data,
      assignees: data.assignees?.map((assignee) => assignee.id),
      status: data.status as StatusEnum,
    })
      .then(async () => {
        await invalidateQueries();
        onHide();
      })
      .catch(async (error) => {
        if (isAxiosError(error) && error.response?.status === 404) {
          await invalidateQueries();
        }
        setError('description', {
          message: getErrorMessage(error),
          type: 'backend',
        });
      })
      .finally(() => {
        setLoading(false);
      });
  };

  const renderFooter = () => {
    return (
      <div>
        <ConfirmPopup />
        <Button
          className="p-button-text"
          disabled={loading}
          icon="pi pi-times"
          label="Mégsem"
          onClick={onHide}
        />
        <Button
          autoFocus
          icon="pi pi-check"
          label="Mentés"
          loading={loading}
          onClick={handleSubmit(onSubmit)}
        />
      </div>
    );
  };

  const renderHeader = () => {
    return (
      <div className="align-items-center flex justify-content-start">
        {todoId ? (
          <span>Feladat módosítása</span>
        ) : (
          <span>Feladat létrehozása</span>
        )}

        {loading && (
          <ProgressSpinner
            style={{
              height: '1.25rem',
              marginLeft: '1rem',
              width: '1.25rem',
            }}
          />
        )}
      </div>
    );
  };

  const statusTemplate = (option: number) => {
    return <TodoStatusTag statusNum={option} />;
  };

  return (
    <Dialog
      closeOnEscape={!isDirty}
      breakpoints={{ '768px': '95vw' }}
      footer={renderFooter}
      header={renderHeader}
      onHide={onHide}
      style={{ width: '50vw' }}
      visible={visible}
      {...props}
      {...ref}
    >
      <form className="formgrid grid p-fluid">
        <div className="field col-12">
          <label className="font-medium text-900 text-sm" htmlFor="status">
            Státusz
          </label>
          <Controller
            control={control}
            disabled={loading}
            name="status"
            render={({ field, fieldState }) => (
              <>
                <Dropdown
                  {...field}
                  id={field.name}
                  itemTemplate={statusTemplate}
                  options={Object.values(StatusEnum)}
                  valueTemplate={statusTemplate}
                />
                {fieldState.error && (
                  <small className="block p-error" id={field.name + '-help'}>
                    {fieldState.error.message}
                  </small>
                )}
              </>
            )}
          />
        </div>
        <div className="field col-12">
          <label className="font-medium text-900 text-sm" htmlFor="description">
            Leírás
          </label>
          <Controller
            control={control}
            disabled={loading}
            name="description"
            render={({ field, fieldState }) => (
              <>
                <InputTextarea {...field} autoResize id={field.name} rows={5} />
                {fieldState.error && (
                  <small className="block p-error" id={field.name + '-help'}>
                    {fieldState.error.message}
                  </small>
                )}
              </>
            )}
          />
        </div>
        <div className="field col-12">
          <label className="font-medium text-900 text-sm" htmlFor="assignees">
            Felelősök
          </label>
          <Controller
            control={control}
            disabled={loading}
            name="assignees"
            render={({ field, fieldState }) => (
              <>
                <AutoCompleteStaffMultiple
                  {...field}
                  className="w-full"
                  id={field.name}
                />
                {fieldState.error && (
                  <small className="block p-error" id={field.name + '-help'}>
                    {fieldState.error.message}
                  </small>
                )}
              </>
            )}
          />
        </div>
        {isDirty && !!todoId && !loading && (
          <div className="col-12">
            <Message
              className="justify-content-start"
              severity="warn"
              text="A módosításaid még nincsenek elmentve!"
            />
          </div>
        )}
      </form>
    </Dialog>
  );
});
TodoDialog.displayName = 'TodoDialog';

export default TodoDialog;
