export type Semester = {
  afterDate: Date;
  beforeDate: Date;
  name: string;
};

export function getLatestSemester() {
  return getSemesters()[1];
}

export function getSemesters() {
  const semesters: Semester[] = [];

  semesters.push({
    afterDate: new Date(0),
    beforeDate: new Date('2021-06-30'),
    name: 'Korábbi',
  });

  semesters.push({
    afterDate: new Date('2021-07-01'),
    beforeDate: new Date('2021-12-31'),
    name: '2021/22/1',
  });

  const currentDate = new Date();
  const firstYear = 2022;
  const lastYear = currentDate.getFullYear();

  for (let year = firstYear; year <= lastYear; year++) {
    semesters.push({
      afterDate: new Date(`${year}-01-01`),
      beforeDate: new Date(`${year}-06-30`),
      name: `${year - 1}/${year.toString().slice(-2)}/2`,
    });

    if (year !== lastYear || (year === lastYear && currentDate.getMonth() >= 6))
      semesters.push({
        afterDate: new Date(`${year}-07-01`),
        beforeDate: new Date(`${year}-12-31`),
        name: `${year}/${(year + 1).toString().slice(-2)}/1`,
      });
  }

  const lastSemester = semesters[semesters.length - 1];
  const laterAfterDate = new Date(lastSemester.beforeDate);
  laterAfterDate.setDate(laterAfterDate.getDate() + 1);

  semesters.push({
    afterDate: laterAfterDate,
    beforeDate: new Date('2100-12-31'),
    name: 'Későbbi',
  });

  return semesters.reverse();
}
