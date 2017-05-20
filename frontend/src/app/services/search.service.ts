import { Injectable } from "@angular/core";
import { Headers, Http, RequestOptions, Response } from "@angular/http";
import { Observable } from "rxjs/Observable";
import { BehaviorSubject } from "rxjs/Rx";
import { Subscription } from "rxjs/Subscription";
import "rxjs/add/operator/map";
import "rxjs/add/operator/catch";
import { CampSite, FreePark, Search } from "../models";

@Injectable()
export class SearchService {
    private baseUrl = process.env.SEARCH_SERVICE_URL;
    private parkSearchUrl = this.baseUrl + '/parks/free';
    private freeParksSubject: BehaviorSubject<FreePark[]> = new BehaviorSubject([]);
    private freeSitesSubject: BehaviorSubject<CampSite[]> = new BehaviorSubject([]);
    private lastSearch: Search;

    constructor(private http: Http) {
    }

    public clearFreeParks() {
        this.freeParksSubject.next([]);
    }

    public searchFreeParks(search: Search) {
        this.lastSearch = search;
        let headers = new Headers({'Content-Type': 'application/json'});
        let options = new RequestOptions({
            search: search.toQuery(),
            headers
        });

        return this.http.get(this.parkSearchUrl, options)
            .map((resp) => this.extractFreeParks(resp))
            .map((freeParks) => {
                this.freeParksSubject.next(freeParks);
                return freeParks;
            })
            .catch(this.handleError);
    }

    public subscribeFreeParks(fn: (_: FreePark[]) => void): Subscription {
        return this.freeParksSubject.asObservable().subscribe(fn);
    }

    public searchFreeSites(parkName: string) {
        let search = this.lastSearch;
        let headers = new Headers({'Content-Type': 'application/json'});
        let options = new RequestOptions({
            search: search.toQuery(),
            headers
        });

        let siteSearchUrl = this.baseUrl + '/parks/' + parkName + '/campsites/free';
        return this.http.get(siteSearchUrl, options)
            .map((resp) => resp.json().data as CampSite[])
            .map((campSites) => {
                this.freeSitesSubject.next(campSites);
                return campSites;
            })
            .catch(this.handleError);
    }

    public subscribeFreeSites(fn: (_: CampSite[]) => void): Subscription {
        return this.freeSitesSubject.asObservable().subscribe(fn);
    }

    private extractFreeParks(resp) {
        return resp.json().data as FreePark[];
    }

    private handleError(error: any): Observable<any> {
        let errMsg: string;
        if (error instanceof Response) {
            const body = error.json() || '';
            const err = body.error || JSON.stringify(body);
            errMsg = `${error.status} - ${error.statusText || ''} ${err}`;
        } else {
            errMsg = error.message ? error.message : error.toString();
        }
        console.error(errMsg);
        return Observable.throw(errMsg);
    }
}
