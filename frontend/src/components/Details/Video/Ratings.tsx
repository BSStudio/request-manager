import { MouseEventHandler, useState } from 'react';

import { useQuery } from '@tanstack/react-query';
import { Avatar } from 'primereact/avatar';
import { Button } from 'primereact/button';
import { Dropdown } from 'primereact/dropdown';
import { ProgressBar } from 'primereact/progressbar';
import { Tooltip } from 'primereact/tooltip';
import { classNames } from 'primereact/utils';

import { RatingAdminListRetrieve } from 'api/models';
import { requestVideoRatingsListQuery } from 'api/queries';
import RatingDialog from 'components/RatingDialog/RatingDialog';
import { dateTimeToLocaleString } from 'helpers/DateToLocaleStringCoverters';
import { getUserId, isAdmin } from 'helpers/LocalStorageHelper';
import TimeAgo from 'helpers/TimeAgo';
import { UI_AVATAR_URL } from 'localConstants';

interface RatingAdminListDates // TODO: Rename?
  extends Omit<RatingAdminListRetrieve, 'created'> {
  created: Date;
}

type RatingProps = {
  authorName: string;
  avatarUrl?: string;
  creationDate: Date;
  onEdit: MouseEventHandler<HTMLButtonElement>;
  rating: number;
  review: string;
  showEdit: boolean;
};

type RatingSummaryProps = {
  portion: number;
  rating: number;
};

type RatingsProps = {
  avgRating: number;
  isRated: boolean;
  requestId: number;
  videoId: number;
  videoStatus: number;
  videoTitle: string;
};

const Rating = ({
  authorName,
  avatarUrl,
  creationDate,
  onEdit,
  rating,
  review,
  showEdit,
}: RatingProps) => {
  return (
    <div className="col-12 lg:col-6">
      <div className="p-2">
        <div className="border-1 border-round p-3 surface-border">
          <div className="align-items-center flex mb-3">
            <Tooltip className="text-xs" target=".created-date-text" />
            <Avatar
              className="flex-shrink-0 h-2rem mr-2 w-2rem"
              icon="pi pi-user"
              image={avatarUrl || UI_AVATAR_URL + authorName}
              shape="circle"
            />
            <span className="font-medium mr-3 text-900">{authorName}</span>
            <span
              className="created-date-text font-medium text-500 text-sm"
              data-pr-position="bottom"
              data-pr-tooltip={dateTimeToLocaleString(creationDate)}
            >
              <TimeAgo datetime={creationDate} locale="hu_HU" />
            </span>
            <span className="ml-auto">
              {[...Array(5).keys()].map((item) => (
                <i
                  className={classNames('pi pi-star-fill', {
                    'mr-1': item < 4,
                    'text-300': rating <= item,
                    'text-yellow-500': rating > item,
                  })}
                  key={item}
                ></i>
              ))}
            </span>
          </div>
          <p className="comment-text line-height-3 m-0 p-0 text-600">
            {review}
          </p>
          {showEdit && (
            <div className="flex flex-wrap justify-content-end">
              <Button
                className="p-1"
                icon="pi pi-pencil"
                label="Szerkesztés"
                onClick={onEdit}
                size="small"
                text
              />
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

const RatingSummary = ({ portion, rating }: RatingSummaryProps) => {
  return (
    <li className="align-items-center flex mb-2">
      <span className="font-medium mr-2 text-900 w-1rem">{rating}</span>
      <div
        style={{ height: '7px' }}
        className="border-round flex-auto overflow-hidden surface-300"
      >
        {portion > 0 && (
          <div className={`bg-yellow-500 border-round h-full w-${portion}`} />
        )}
      </div>
    </li>
  );
};

const Ratings = ({
  avgRating,
  isRated,
  requestId,
  videoId,
  videoStatus,
  videoTitle,
}: RatingsProps) => {
  const { data = [], isLoading } = useQuery({
    ...requestVideoRatingsListQuery(requestId, videoId),
    select: (ratings): RatingAdminListDates[] =>
      ratings.map((rating) => ({
        ...rating,
        created: new Date(rating.created),
      })),
  });

  const [ordering, setOrdering] = useState<
    'highest' | 'lowest' | 'oldest' | 'newest'
  >('newest');
  const [ratingDialogAuthorName, setRatingDialogAuthorName] =
    useState<string>('');
  const [ratingDialogId, setRatingDialogId] = useState<number>(0);
  const [ratingDialogVisible, setRatingDialogVisible] =
    useState<boolean>(false);

  const orderingOptions = [
    { name: 'Legújabb', value: 'newest' },
    { name: 'Legrégebbi', value: 'oldest' },
    { name: 'Legjobb', value: 'highest' },
    { name: 'Legrosszabb', value: 'lowest' },
  ];

  const onRatingDialogHide = () => {
    setRatingDialogVisible(false);
    setRatingDialogAuthorName('');
    setRatingDialogId(0);
  };

  const onRatingEdit = (authorName: string, ratingId: number) => {
    setRatingDialogVisible(true);
    setRatingDialogAuthorName(authorName);
    setRatingDialogId(ratingId);
  };

  const numberOfRating = (rating: number) => {
    return data.reduce(
      (total, next) => (next.rating == rating ? total + 1 : total),
      0,
    );
  };

  function compare(a: RatingAdminListDates, b: RatingAdminListDates) {
    if (ordering === 'highest') {
      if (a.rating - b.rating !== 0) {
        return b.rating - a.rating;
      }
    } else if (ordering === 'lowest') {
      if (a.rating - b.rating !== 0) {
        return a.rating - b.rating;
      }
    } else if (ordering === 'oldest') {
      return a.created.getTime() - b.created.getTime();
    }
    return b.created.getTime() - a.created.getTime();
  }

  return (
    <>
      <RatingDialog
        isRated={isRated}
        onHide={onRatingDialogHide}
        ratingAuthorName={ratingDialogAuthorName}
        ratingId={ratingDialogId}
        requestId={requestId}
        videoId={videoId}
        videoTitle={videoTitle}
        visible={ratingDialogVisible}
      />
      <div className="flex flex-column md:flex-row">
        <div className="md:w-6 w-full">
          <ul className="list-none m-0 p-0">
            {[...Array(5).keys()].reverse().map((item) => (
              <RatingSummary
                key={item}
                portion={Math.round(
                  (numberOfRating(item + 1) / data.length) * 12,
                )}
                rating={item + 1}
              />
            ))}
          </ul>
        </div>
        <div className="align-items-center flex flex-column justify-content-center md:mt-0 md:w-6 mt-4 w-full">
          <span className="font-medium mb-3 text-900 text-5xl">
            {(avgRating || 0).toFixed(2)}
          </span>
          <span className="mb-2">
            {[...Array(5).keys()].map((item) => (
              <i
                className={classNames('pi pi-star-fill text-2xl', {
                  'mr-1': item < 4,
                  'text-300': Math.round(avgRating) <= item,
                  'text-yellow-500': Math.round(avgRating) > item,
                })}
                key={item}
              ></i>
            ))}
          </span>
          <a
            tabIndex={0}
            className="cursor-pointer font-medium hover:text-blue-600 text-blue-500 transition-colors transition-duration-300"
          >
            {`${data.length} Értékelés`}
          </a>
        </div>
      </div>
      <div className="border-top-1 mt-5 pt-5 surface-border">
        <div className="align-items-center flex justify-content-between mb-5">
          <Button
            disabled={videoStatus < 3}
            label={isRated ? 'Értékelés szerkesztése' : 'Értékelés írása'}
            onClick={() => {
              setRatingDialogVisible(true);
            }}
          />
          <Dropdown
            onChange={(e) => {
              setOrdering(e.value);
            }}
            options={orderingOptions}
            optionLabel="name"
            value={ordering}
          />
        </div>
        <div className="grid -ml-3 -mr-3 -mt-3">
          {isLoading ? (
            <div className="p-3 w-full">
              <ProgressBar mode="indeterminate" />
            </div>
          ) : (
            [...data].sort(compare).map((rating) => (
              <Rating
                authorName={rating.author.full_name}
                avatarUrl={rating.author.avatar_url}
                creationDate={rating.created}
                key={rating.id}
                onEdit={() => {
                  onRatingEdit(rating.author.full_name, rating.id);
                }}
                rating={rating.rating}
                review={rating.review}
                showEdit={rating.author.id === getUserId() || isAdmin()}
              />
            ))
          )}
        </div>
      </div>
    </>
  );
};

export default Ratings;
