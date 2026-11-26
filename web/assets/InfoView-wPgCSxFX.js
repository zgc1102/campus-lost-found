import{o as c,c as l,a as t,t as n,A as s}from"./index-cSHso43s.js";const d={class:"screen active",id:"screen-info"},r={class:"topbar"},p={class:"t"},_={class:"scroll"},y={class:"form-card",style:{padding:"18px"}},b={style:{"font-size":"12px","line-height":"1.9",color:"var(--ink)","white-space":"pre-wrap"}},u={__name:"InfoView",props:{infoKey:{type:String,default:"about"}},emits:["nav"],setup(i,{emit:f}){const e={about:{title:"平台简介",body:"清华校园拾光里是一个面向校园的失物招领与爱心互助平台。我们希望把散落在各个群里的失物信息集中起来，让捡到的人更快找到失主，也让需要帮忙的人更容易被看见。"},contact:{title:"联系方式",body:`项目由清华学生团队维护，仅用于校园公益。
反馈与建议：可在「我的发布」留言，或联系项目组同学。
紧急情况请联系保卫部：010-62782001。`},legal:{title:"法律声明",body:`平台仅提供信息发布与匹配服务，不对线下交接过程作担保。请勿发布违法、危险或侵犯他人隐私的内容。
涉及证件、贵重物品时，请当面核对特征，谨防冒领与诈骗。`},privacy:{title:"隐私权保护",body:`完整手机号只用于失物联系，列表页默认打码。
认领留言只用于发布者核对，不对外展示联系方式。
上传的照片仅用于失物展示与审核。`},faq:{title:"来清华常问的问题",body:`访客进校：请通过「参观清华」官方渠道预约，持身份证从指定校门入校。
校园卡丢了：先在校卡系统挂失，再到附近食堂/图书馆服务台和失物招领点询问。
食堂：观畴园、清芬园、桃李园、紫荆园等都对师生开放，访客可扫码支付。`},phones:{title:"常用电话",body:`校医院急诊（24 小时）：010-62782185
24 小时心理服务热线：010-62785252
保卫部 24 小时报警求助：010-62782001
保卫部值班（备用）：010-62783779
后勤综合服务热线 / 校内查号台：010-62793001
学生公寓 24 小时服务热线：010-62793003
本科生招生办公室：010-62770334
研究生招生办公室：010-62781380`}}[i.infoKey]||{title:"说明",body:"暂无内容。"};return(a,o)=>(c(),l("section",d,[t("div",r,[t("div",{class:"back",onClick:o[0]||(o[0]=m=>a.$emit("nav","guide"))},"‹"),t("div",p,n(s(e).title),1)]),t("div",_,[t("div",y,[t("p",b,n(s(e).body),1)])])]))}};export{u as default};
