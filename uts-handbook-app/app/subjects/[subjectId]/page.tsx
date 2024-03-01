import prisma from "@/app/utils/prisma";
import Image from "next/image";
import Markdown from "markdown-to-jsx";
import Link from "next/link";
import { ReactNode } from "react";

function capitalizeFirstLetter(string: string) {
  return string.charAt(0).toUpperCase() + string.slice(1);
}

async function getData(subjectId: string) {
  const subject = await prisma.subject.findUnique({
    where: { id: subjectId },
  });
  return { subject };
}

const MdH1H2 = ({ children }: { children: string }) => (
  <h3 className="text-2xl font-bold">{children}</h3>
);

const MdH3 = ({ children }: { children: string }) => (
  <h3 className="text-2xl font-bold">{children}</h3>
);

const MdH4 = ({ children }: { children: string }) => (
  <h4 className="text-lg font-bold">{children}</h4>
);

const MdA = ({ children, href }: { children: string; href: string }) => (
  <Link href={href} className="text-blue hover:text-blue-light">
    {children}
  </Link>
);

const MdTable = ({ children }: { children: ReactNode }) => (
  <table className="my-4">{children}</table>
);

const MdTh = ({ children }: { children: string }) => (
  <th className="text-left">{children}</th>
);

const MdTr = ({ children }: { children: ReactNode }) => <tr>{children}</tr>;

const MdTd = ({ children }: { children: string }) => (
  <td className="py-2 pr-4 text-left">{children}</td>
);

const options = {
  overrides: {
    h1: {
      component: MdH1H2,
    },
    h2: {
      component: MdH1H2,
    },
    h3: {
      component: MdH3,
    },
    h4: {
      component: MdH4,
    },
    a: {
      component: MdA,
    },
    table: {
      component: MdTable,
    },
    th: {
      component: MdTh,
    },
    tr: {
      component: MdTr,
    },
    td: {
      component: MdTd,
    },
  },
};

// all components are server side rendered by default
export default async function Page({
  params,
}: {
  params: { subjectId: string };
}) {
  const data = await getData(params.subjectId);

  if (!data || !data.subject) {
    return <div>Subject not found</div>;
  }

  const {
    subject: {
      id,
      name,
      sessions,
      creditPoints,
      resultType,
      content,
      requisites,
      antiRequisites,
    },
  } = data;

  const sessions_text = sessions
    .map((s) => capitalizeFirstLetter(s.toLowerCase()))
    .join(", ");

  return (
    <>
      {data && data.subject && (
        <main>
          <div className="w-full">
            <div className="flex w-full items-center justify-start bg-black">
              <Image
                alt="UTS logo"
                src="/uts-logo.png"
                width="100"
                height="100"
              />

              <div className="w-full">
                <h1 className="text-center text-3xl font-bold text-white">
                  University of Technology Sydney Handbook
                </h1>
              </div>
            </div>

            <div className="p-16">
              <div className="mx-auto flex max-w-screen-lg flex-col items-start justify-start gap-4">
                <h2 className="text-3xl font-bold">
                  {id}: {name}
                </h2>

                <h3 className="text-lg">
                  Credit points: {creditPoints}cp | Sessions: {sessions_text} |
                  Result type: {resultType}
                </h3>

                <h3 className="text-lg">
                  Requisites:{" "}
                  {requisites
                    .map((r) => {
                      r = r as { id: string; name: string };
                      return `${r.id} ${r.name}`;
                    })
                    .join(", ")}
                </h3>

                <h3 className="text-lg">
                  AntiRequisites:{" "}
                  {antiRequisites
                    .map((r) => {
                      r = r as { id: string; name: string };
                      return `${r.id} ${r.name}`;
                    })
                    .join(", ")}
                </h3>

                <Markdown
                  className="flex flex-col items-start justify-start gap-4"
                  options={options}
                >
                  {content}
                </Markdown>
              </div>
            </div>
          </div>
        </main>
      )}
    </>
  );
}