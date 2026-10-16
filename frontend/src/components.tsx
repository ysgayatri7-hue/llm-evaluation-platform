import{ReactNode}from'react';import{AlertTriangle,Database,FlaskConical,LayoutDashboard,PlayCircle,Scale,FileText,Tags}from'lucide-react';
export const nav=[['Dashboard',LayoutDashboard],['Datasets',Database],['Configure',FlaskConical],['Runner',PlayCircle],['Results',Scale],['Human review',Tags],['Reports',FileText]]as const;
export function Card({children,className=''}:{children:ReactNode,className?:string}){return <section className={`card ${className}`}>{children}</section>}
export function Empty({children}:{children:ReactNode}){return <div className="empty"><AlertTriangle size={24}/><p>{children}</p></div>}
export function Score({value}:{value:number|null|undefined}){if(value==null)return <span className="muted">Skipped</span>;let tone=value>=.8?'good':value>=.5?'mid':'bad';return <span className={`score ${tone}`}>{(value*100).toFixed(0)}</span>}
export function Badge({children,tone='neutral'}:{children:ReactNode;tone?:string}){return <span className={`badge ${tone}`}>{children}</span>}

